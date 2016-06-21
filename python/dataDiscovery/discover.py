import datetime
import logging
import re
import sqlalchemy

import utils.workflows as workflows
import dbs.apis.dbsClient as dbsapi
import logs.logger as logs
import t0wmadatasvcApi.t0wmadatasvcApi as t0wmadatasvcApi

from rrapi.rrapi_v3 import RRApi, RRApiError
from model import Base, RunInfo, RunBlock, Multirun, Filename


def get_base_release(full_release):
    pattern = r'(?P<release>CMSSW_\d+_\d+_)\d+'
    base_release = re.match(pattern, full_release)
    if not base_release:
        raise ValueError("Couldn't determine base release out of {}".format(full_release))
    return base_release.group('release')


def discover(config):
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(config['runs_db_path']), echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    rrapi = RRApi(config['rrapi_url'], debug=True)
    dbsApi = dbsapi.DbsApi(url=config['dbsapi_url'])

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

    complete_runs = [run.number for run in local_runs if run.stop_time]
    incomplete_runs = [run.number for run in local_runs if not run.stop_time]

    logger.info("Updating local database of new fetched runs")
    for run in valid_runs:

        logger.debug("Checking run {} fetched from Run Registry".format(run[u'number']))

        if run[u'number'] in complete_runs:
            logger.debug("Run {} already exists in local database".format(run[u'number']))
            continue

        if run[u'number'] in incomplete_runs:
            logger.debug("Run {} already exists in local database but does not has a stop date".format(run[u'number']))

            if run[u'stopTime']:
                logger.info("Updating incomplete run {} ".format(run[u'number']))
                start = datetime.datetime.strptime(run[u'startTime'], "%a %d-%m-%y %H:%M:%S")
                stop = datetime.datetime.strptime(run[u'stopTime'], "%a %d-%m-%y %H:%M:%S")
                old_run = session.query(RunInfo).filter(RunInfo.number == run[u'number'])
                old_run.run_class_name = run[u'runClassName']
                old_run.bfield = run[u'bfield']
                old_run.start_time = start
                old_run.stop_time = stop
            else:
                logger.debug("Run {} still without stop time".format(run[u'number']))
                continue

        else:
            logger.info("New run: {}".format(run[u'number']))
            start = datetime.datetime.strptime(run[u'startTime'], "%a %d-%m-%y %H:%M:%S")
            stop = None
            try:
                stop = datetime.datetime.strptime(run[u'stopTime'], "%a %d-%m-%y %H:%M:%S")
            except TypeError:
                # if there is not stop date we can ignore it
                pass
            run_info = RunInfo(number=run[u'number'], run_class_name=run[u'runClassName'], bfield=run[u'bfield'],
                               start_time=start, stop_time=stop)
            session.add(run_info)

        session.commit()

    logger.info("Getting complete runs from local database")
    # TODO #12: the second condition ignores harvest_all_runs config value
    complete_runs = session.query(RunInfo).filter(RunInfo.stop_time != None,
                                                  RunInfo.start_time > days_old_runs_date).all()
    # TODO #1: test if the date comparison works properly

    t0api = t0wmadatasvcApi.Tier0Api()
    logger.info("Starting creating multiruns...")
    for run in complete_runs:

        logger.debug("Retrieving express config for run {}".format(run.number))
        release = t0api.get_run_info(run.number)
        if not release:
            logger.debug("Express config for run {} is not available".format(run.number))
            continue

        base_release = get_base_release(release['cmssw'])
        base_release_pattern = "{}%".format(base_release)

        logger.debug("Getting already harvested blocks for run {}".format(run.number))
        harvested_blocks = session.query(RunBlock.block_name).filter(RunBlock.run_number == run.number).all()
        harvested_blocks_list = list()
        for block_name, in harvested_blocks:
            harvested_blocks_list.append(block_name)

        datasets = dbsApi.listDatasets(run_num=run.number, dataset='/*/*/ALCAPROMPT')
        for dataset in datasets:

            files, number_of_events = [], 0

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

            logger.debug("Getting not harvested blocks for dataset {}".format(dataset['dataset']))
            blocks = dbsApi.listBlocks(run_num=run.number, dataset=dataset['dataset'])
            new_blocks = list()
            for block in blocks:
                if block['block_name'] not in harvested_blocks_list:
                    new_blocks.append(RunBlock(block_name=block['block_name'], run_number=run.number))

            # so not to create multiruns when they will not have any files - a common situation
            if new_blocks:
                multirun = session.query(Multirun).filter(Multirun.dataset == dataset['dataset'],
                                                          Multirun.closed == False,
                                                          Multirun.bfield == run.bfield,
                                                          Multirun.run_class_name == run.run_class_name,
                                                          Multirun.cmssw.like(base_release_pattern),
                                                          # TODO: write tests to find out whether it really works as wanted
                                                          Multirun.scram_arch == release['scram_arch'],
                                                          Multirun.scenario == release['scenario'],
                                                          Multirun.global_tag == release['global_tag']).one_or_none()
                # TODO #4 - release should be equal up to 2 digits?

                if not multirun:
                    multirun = Multirun(number_of_events=number_of_events, dataset=dataset['dataset'],
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

                logger.debug("Getting files and number of events from new blocks for multirun {}".format(multirun.id))
                for block in new_blocks:
                    session.add(block)
                    block_files = dbsApi.listFiles(run_num=run.number, block_name=block.block_name)
                    files.extend(block_files)
                    file_summaries = dbsApi.listFileSummaries(run_num=run.number, block_name=block.block_name)
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

    session.commit()
