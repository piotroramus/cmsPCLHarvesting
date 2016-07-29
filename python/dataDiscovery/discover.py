import datetime
import logging
import re
import sqlalchemy

import utils.workflows as workflows
import dbsApi.DBSApi as dbsapi
import logs.logger as logs
import t0wmadatasvcApi.t0wmadatasvcApi as t0wmadatasvcApi
import rrapi.rrapi_wrapper as rrApi

from model import RunInfo, Multirun, Filename, Dataset, MultirunState


def get_base_release(full_release):
    pattern = r'^(?P<release>CMSSW_\d+_\d+_)\d+_?'
    base_release = re.match(pattern, full_release)
    if not base_release:
        raise ValueError("Couldn't determine base release out of {}".format(full_release))
    return base_release.group('release')


def get_run_class_names(workflow_run_classes):
    run_class_names = set()
    for workflow_list in workflow_run_classes.itervalues():
        for workflow in workflow_list:
            run_class_names.add(workflow)
    return run_class_names


def update_runs(logger, session, t0api, config, local_runs, recent_runs):
    stream_timeout = datetime.date \
        .fromordinal(datetime.date.today().toordinal() - config['run_stream_timeout']) \
        .strftime("%Y-%m-%d")

    complete_stream_runs = [run.number for run in local_runs if run.stream_completed]
    incomplete_stream_runs = [run.number for run in local_runs if not run.stream_completed]

    logger.info("Updating local database with newly fetched runs")
    for run in recent_runs:

        logger.debug("Checking run {} fetched from Run Registry".format(run[u'runnumber']))

        if run[u'runnumber'] in complete_stream_runs:
            logger.debug("Run {} already exists in local database".format(run[u'runnumber']))
            continue

        if run[u'runnumber'] in incomplete_stream_runs:
            logger.debug(
                "Run {} already exists in local database but the stream was not completed".format(run[u'runnumber']))

            if t0api.run_stream_completed(run[u'runnumber']):
                logger.info(
                    "Stream for run {} is now completed. It can be thus included in multi-runs".format(
                        run[u'runnumber']))
                run_to_update = session.query(RunInfo).filter(RunInfo.number == run[u'runnumber']).one()
                run_to_update.stream_completed = True
            else:
                logger.debug("Stream for run {} is still not completed".format(run[u'runnumber']))
                if run[u'starttime'] < stream_timeout:  # TODO: test
                    logger.warning("Stream for run {} is not completed for {} days now.")
                    logger.warning("Run will be processed with the data it has for the moment")
                    timedout_run = session.query(RunInfo).filter(RunInfo.number == run[u'runnumber']).one()
                    timedout_run.stream_timeout = True
                    timedout_run.stream_completed = True
                continue

        else:
            stream_completed = t0api.run_stream_completed(run[u'runnumber'])
            if stream_completed != -1:
                logger.info("New run: {}".format(run[u'runnumber']))
                start = datetime.datetime.strptime(run[u'starttime'], "%Y-%m-%d %H:%M:%S")
                run_info = RunInfo(number=run[u'runnumber'], run_class_name=run[u'runClassName'], bfield=run[u'bfield'],
                                   start_time=start, stream_completed=stream_completed, stream_timeout=False,
                                   used_datasets=[], used=False)
                session.add(run_info)

        session.commit()


def discover(config, session):
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    t0api = t0wmadatasvcApi.Tier0Api()
    rrapi = rrApi.RRApiWrapper(config)

    days_old_runs_date = datetime.date \
        .fromordinal(datetime.date.today().toordinal() - config['days_old_runs'])

    run_class_names = get_run_class_names(config['workflow_run_classes'])

    recent_runs = rrapi.query(days_old_runs_date, run_class_names)

    # TODO: think if this is neeeded - if there is not start date then how the query can work?
    logger.info("Checking if all the runs have start date")
    for run in recent_runs:
        if u'starttime' not in run:
            logger.error("Run without a start date: {}. Ignoring.".format(run[u'runnumber']))
    valid_runs = (r for r in recent_runs if r[u'starttime'])

    logger.info("Getting {} days old runs form local database".format(config['days_old_runs']))
    local_runs = session.query(RunInfo).filter(RunInfo.start_time > days_old_runs_date,
                                               RunInfo.stream_timeout == False).all()

    update_runs(logger, session, t0api, config, local_runs, valid_runs)


def assembly_multiruns(config, session):
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    # TODO 1: dbs_api url from config
    dbsApi = dbsapi.DBSApi()
    t0api = t0wmadatasvcApi.Tier0Api()

    logger.info("Getting runs with completed stream from local database")
    unused_complete_runs = session.query(RunInfo).filter(RunInfo.stream_completed == True,
                                                         RunInfo.used == False).all()

    ready_state = session.query(MultirunState).filter(MultirunState.state == 'ready').one()

    logger.info("Starting to assemble multiruns...")
    for run in unused_complete_runs:

        logger.debug("Retrieving express config for run {}".format(run.number))
        release = t0api.get_run_info(run.number)
        if not release:
            logger.debug("Express config for run {} is not available".format(run.number))
            continue

        base_release = get_base_release(release['cmssw'])
        base_release_pattern = "{}%".format(base_release)

        logger.debug("Getting list of datasets for run {} from DBS".format(run.number))
        run_datasets = dbsApi.listDatasets(run_num=run.number, dataset='/*/*/ALCAPROMPT')

        logger.debug("Getting datasets that are not part of any multi-run for the given run")
        datasets = list()
        used_datasets = [d.dataset for d in run.used_datasets]
        for dataset in run_datasets:
            if dataset['dataset'] not in used_datasets:
                datasets.append(dataset['dataset'])

        for dataset in datasets:

            available_workflows = config['workflow_run_classes'].keys()
            dataset_workflow = workflows.extract_workflow(dataset, available_workflows)
            if dataset_workflow not in release['workflows']:
                logger.warning(
                    "Dataset {} workflow {} is different than workflow from run {} express config: {}".format(
                        dataset, dataset_workflow, run.number, release['workflows']))
                continue

            if run.run_class_name not in config['workflow_run_classes'][dataset_workflow]:
                logger.debug(
                    "Ignoring dataset {} for run {} since runClassName {} for the run is not specified for this dataset workflow {}:{}".format(
                        dataset, run.number, run.run_class_name, dataset_workflow,
                        config['workflow_run_classes'][dataset_workflow]))
                continue

            dataset_object = session.query(Dataset).filter(Dataset.dataset == dataset).one_or_none()
            if not dataset_object:
                logger.info("New dataset: {}".format(dataset))
                dataset_object = Dataset(dataset=dataset)
                session.add(dataset_object)

            logger.debug("Searching for existence of 'ready' or 'processing' multi-run with similar properties")
            not_processed_multirun = session.query(Multirun) \
                .join(MultirunState) \
                .filter(Multirun.dataset == dataset_object,
                        Multirun.bfield == run.bfield,
                        Multirun.run_class_name == run.run_class_name,
                        Multirun.cmssw.like(base_release_pattern),
                        # TODO: write tests to find out whether it really works as wanted
                        Multirun.scram_arch == release['scram_arch'],
                        Multirun.scenario == release['scenario'],
                        Multirun.global_tag == release['global_tag']) \
                .filter(sqlalchemy.or_(MultirunState.state == 'ready', MultirunState.state == 'processing')) \
                .one_or_none()  # TODO: test this or_

            if not_processed_multirun:
                logger.debug(
                    "Multi-run {} found in {} state".format(not_processed_multirun.id, not_processed_multirun.state))
                continue

            logger.debug("Searching for multi-run that the run could be merged into")
            multirun = session.query(Multirun) \
                .join(MultirunState) \
                .filter(Multirun.dataset == dataset_object,
                        Multirun.bfield == run.bfield,
                        Multirun.run_class_name == run.run_class_name,
                        Multirun.cmssw.like(base_release_pattern),
                        Multirun.scram_arch == release['scram_arch'],
                        Multirun.scenario == release['scenario'],
                        Multirun.global_tag == release['global_tag']) \
                .filter(MultirunState.state == 'need_more_data') \
                .one_or_none()

            if not multirun:
                need_more_data_state = session.query(MultirunState).filter(
                    MultirunState.state == 'need_more_data').one()
                multirun = Multirun(number_of_events=0, dataset=dataset_object,
                                    bfield=run.bfield, run_class_name=run.run_class_name,
                                    cmssw=release['cmssw'], scram_arch=release['scram_arch'],
                                    scenario=release['scenario'], global_tag=release['global_tag'],
                                    retries=0, state=need_more_data_state)
                session.add(multirun)
                # force generation of multirun.id which is accessed later on in this code
                session.flush()
                session.refresh(multirun)
                logger.info("Created new multirun {}".format(multirun))

            multirun.run_numbers.append(run)

            # add dataset to used for given run
            run.used_datasets.append(dataset_object)

            # if this is the last dataset in run - mark run as used
            if len(datasets) == 1:
                logger.debug("All datasets for run {} are now used in multi-runs".format(run.number))
                run.used = True

            files, number_of_events = [], 0

            logger.debug("Getting blocks, files and number of events for multi-run {}".format(multirun.id))
            blocks = dbsApi.listBlocks(run_num=run.number, dataset=dataset)
            for block in blocks:
                block_files = dbsApi.listFiles(run_num=run.number, block_name=block['block_name'])
                files.extend(block_files)
                file_summaries = dbsApi.listFileSummaries(run_num=run.number,
                                                          block_name=block['block_name'])
                number_of_events += file_summaries[0]['num_event']

            logger.debug("Adding gathered data to multi-run {} summary".format(multirun.id))
            if number_of_events > 0 and files:
                multirun.number_of_events += number_of_events
                for f in files:
                    multirun_file = Filename(filename=f['logical_file_name'], multirun=multirun.id)
                    session.add(multirun_file)
                if multirun.number_of_events > config['events_threshold']:
                    logger.info(
                        "Multirun {} with {} events ready to be processed".format(multirun.id,
                                                                                  multirun.number_of_events))
                    multirun.state = ready_state

        session.commit()
