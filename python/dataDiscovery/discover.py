import datetime
import logging
import re
import sqlalchemy

import utils.workflows as workflows
import dbs.apis.dbsClient as dbsapi
import logs.logger as logs
import t0wmadatasvcApi.t0wmadatasvcApi as t0wmadatasvcApi

from rrapi.rrapi_v3 import RRApi, RRApiError
from model import Base, RunInfo, RunBlock, Multirun, Filename, Dataset


def get_base_release(full_release):
    pattern = r'(?P<release>CMSSW_\d+_\d+_)\d+'
    base_release = re.match(pattern, full_release)
    if not base_release:
        raise ValueError("Couldn't determine base release out of {}".format(full_release))
    return base_release.group('release')


# TODO: review logger messages after all the changes
def discover(config):
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(config['runs_db_path']), echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    rrapi = RRApi(config['rrapi_url'], debug=True)
    dbsApi = dbsapi.DbsApi(url=config['dbsapi_url'])
    t0api = t0wmadatasvcApi.Tier0Api()

    days_old_runs_date = datetime.date.fromordinal(
        datetime.date.today().toordinal() - config['days_old_runs']).strftime(
        "%Y-%m-%d")
    if config['harvest_all_runs']:
        config['filters']['number'] = "> {}".format(config['first_run_number'])
    else:
        config['filters']['startTime'] = "> {}".format(days_old_runs_date)
    recent_runs = []
    # TODO #13: this try is not coupled well with previous if statement - logger info particularly
    try:
        logger.info("Fetching Run Registry records from last {} days".format(config['days_old_runs']))
        # TODO #11: might be worth to take only runs with the runClassNames from config
        recent_runs = rrapi.data(workspace=config['workspace'], columns=config['columns'], table=config['table'],
                                 template=config['template'], filter=config['filters'])
    except RRApiError:
        logger.error("Error while querying RR API for {} days old runs".format(config['days_old_runs']), exc_info=True)

    logger.info("Ignoring runs with no runClassName specified")
    runs_with_classname = [r for r in recent_runs if r[u'runClassName']]

    logger.info("Checking if all the runs have start date")
    for run in runs_with_classname:
        if u'startTime' not in run:
            logger.error("Run without a start date: {}. Ignoring.".format(run[u'number']))
    valid_runs = (r for r in runs_with_classname if r[u'startTime'])

    logger.info("Getting {} days old runs form local database".format(config['days_old_runs']))
    local_runs = session.query(RunInfo).filter(RunInfo.start_time > days_old_runs_date).all()

    closed_runs = [run.number for run in local_runs if run.stream_completed]
    unclosed_runs = [run.number for run in local_runs if not run.stream_completed]

    logger.info("Updating local database of new fetched runs")
    for run in valid_runs:

        logger.debug("Checking run {} fetched from Run Registry".format(run[u'number']))

        if run[u'number'] in closed_runs:
            logger.debug("Run {} already exists in local database".format(run[u'number']))
            continue

        if run[u'number'] in unclosed_runs:
            logger.debug("Run {} already exists in local database but the stream is not closed".format(run[u'number']))

            # if t0api.run_stream_completed(run[u'number']):
            if t0api.fixed_run_stream_completed(run[u'number'], run[u'runClassName']):
                logger.info(
                    "Stream for run {} is now completed. Now it can be included in multiruns".format(run[u'number']))
                old_run = session.query(RunInfo).filter(RunInfo.number == run[u'number'])
                old_run.stream_completed = True
            else:
                # TODO: timeout for not closed streams (few days)
                logger.debug("Stream for run {} still not closed".format(run[u'number']))
                continue

        else:
            logger.info("New run: {}".format(run[u'number']))
            start = datetime.datetime.strptime(run[u'startTime'], "%a %d-%m-%y %H:%M:%S")
            # stream_completed = t0api.run_stream_completed(run[u'number'])
            stream_completed = t0api.fixed_run_stream_completed(run[u'number'], run[u'runClassName'])
            if stream_completed != -1:
                run_info = RunInfo(number=run[u'number'], run_class_name=run[u'runClassName'], bfield=run[u'bfield'],
                                   start_time=start, stream_completed=stream_completed, used_datasets=[], used=False)
                session.add(run_info)

        session.commit()

    logger.info("Getting complete runs from local database")
    # TODO #12: the second condition ignores harvest_all_runs config value
    # complete_runs = session.query(RunInfo).filter(RunInfo.stream_completed == True,
    #                                               RunInfo.start_time > days_old_runs_date).all()

    complete_runs = session.query(RunInfo).filter(RunInfo.stream_completed == True,
                                                  RunInfo.used == False).all()
    # TODO #1: test if the date comparison works properly

    # print "COMPLETED runs: {}".format(complete_runs)

    logger.info("Starting creating multiruns...")
    for run in complete_runs:

        logger.debug("Retrieving express config for run {}".format(run.number))
        release = t0api.get_run_info(run.number)
        if not release:
            logger.debug("Express config for run {} is not available".format(run.number))
            continue

        base_release = get_base_release(release['cmssw'])
        base_release_pattern = "{}%".format(base_release)

        run_datasets = dbsApi.listDatasets(run_num=run.number, dataset='/*/*/ALCAPROMPT')

        # get datasets that are not part of any multi-run yet
        datasets = list()
        used_datasets = [d.dataset for d in run.used_datasets]
        for dataset in run_datasets:
            if dataset['dataset'] not in used_datasets:
                datasets.append(dataset)
                # TODO: change here to datasets.append(dataset['dataset']) and then everywhere below


        for dataset in datasets:

            # TODO logger msg is definitely wrong
            logger.debug("Getting multirun for the dataset {} for run {}".format(dataset['dataset'], run.number))
            dataset_workflow = workflows.extract_workflow(dataset['dataset'])
            if dataset_workflow not in release['workflows']:
                logger.warning(
                    "Dataset {} workflow {} is different than workflow from run {} release {}".format(
                        dataset['dataset'], dataset_workflow, run.number, release['workflows']))
                continue

            if run.run_class_name not in config['workflow_run_classes'][dataset_workflow]:
                logger.debug(
                    "Ignoring dataset {} for run {} since runClassName {} for the run is not specified for this dataset workflow {}:{}".format(
                        dataset['dataset'], run.number, run.run_class_name, dataset_workflow,
                        config['workflow_run_classes'][dataset_workflow]))
                continue

            ds = session.query(Dataset).filter(Dataset.dataset == dataset['dataset']).one_or_none()
            if not ds:
                ds = Dataset(dataset=dataset['dataset'])
                session.add(ds)

            # TODO: search for an open multirun with these properties - if exists then abort processing
            not_processed_multirun = session.query(Multirun).filter(Multirun.processed == False,
                                                                    Multirun.closed == True,
                                                                    Multirun.dataset == dataset['dataset'],
                                                                    # TODO: switch to ds object
                                                                    Multirun.bfield == run.bfield,
                                                                    Multirun.run_class_name == run.run_class_name,
                                                                    Multirun.cmssw.like(base_release_pattern),
                                                                    # TODO: write tests to find out whether it really works as wanted
                                                                    Multirun.scram_arch == release['scram_arch'],
                                                                    Multirun.scenario == release['scenario'],
                                                                    Multirun.global_tag == release[
                                                                        'global_tag']).one_or_none()
            # TODO #4 - release should be equal up to 2 digits?

            if not_processed_multirun:
                continue

            multirun = session.query(Multirun).filter(Multirun.dataset == dataset['dataset'],
                                                      Multirun.closed == False,
                                                      Multirun.bfield == run.bfield,
                                                      Multirun.run_class_name == run.run_class_name,
                                                      Multirun.cmssw.like(base_release_pattern),
                                                      Multirun.scram_arch == release['scram_arch'],
                                                      Multirun.scenario == release['scenario'],
                                                      Multirun.global_tag == release['global_tag']).one_or_none()

            if not multirun:
                # TODO: check if fields are still consistent with model
                multirun = Multirun(number_of_events=0, dataset=dataset['dataset'],
                                    bfield=run.bfield,
                                    run_class_name=run.run_class_name, closed=False, processed=False,
                                    cmssw=release['cmssw'], scram_arch=release['scram_arch'],
                                    scenario=release['scenario'], global_tag=release['global_tag'])
                session.add(multirun)
                # force generation of multirun.id which is accessed later on in this code
                session.flush()
                session.refresh(multirun)
                logger.info("Created new multirun {}".format(multirun))

            multirun.run_numbers.append(run)

            # add dataset to used for given run
            run.used_datasets.append(ds)

            # if this is the last dataset - mark run as used
            if len(datasets) == 1:
                run.used = True

            files, number_of_events = [], 0

            logger.debug("Getting files and number of events from new blocks for multirun {}".format(multirun.id))
            blocks = dbsApi.listBlocks(run_num=run.number, dataset=dataset['dataset'])
            for block in blocks:
                run_block = RunBlock(block_name=block['block_name'], run_number=run.number)
                session.add(run_block)
                block_files = dbsApi.listFiles(run_num=run.number, block_name=run_block.block_name)
                files.extend(block_files)
                file_summaries = dbsApi.listFileSummaries(run_num=run.number,
                                                          block_name=run_block.block_name)  # TODO: measure what is faster: dict or objetct access and adjust properly
                number_of_events += file_summaries[0]['num_event']

            logger.debug("Adding gathered data to multirun {}".format(multirun.id))
            if number_of_events > 0 and files:
                multirun.number_of_events += number_of_events
                for f in files:
                    multirun_file = Filename(filename=f['logical_file_name'], multirun=multirun.id)
                    session.add(multirun_file)
                if multirun.number_of_events > config['events_threshold']:
                    logger.info(
                        "Multirun {} with {} events ready to be processed".format(multirun.id,
                                                                                  multirun.number_of_events))
                    multirun.closed = True

        session.commit()
