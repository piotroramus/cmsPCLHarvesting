import datetime
import logging

from dbs.apis.dbsClient import DbsApi

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rrapi import RRApi, RRApiError
from logs.logger import setup_logging

from model import Base, RunInfo, RunBlock, Multirun, Filename, Workflow
from config import dbsapi_url, rrapi_url, runs_db_path, first_run_number, harvest_all_runs, days_old_runs
from config import workspace, columns, table, template, filters, events_threshold
from t0wmadatasvcApi.t0wmadatasvcApi import Tier0Api


def discover():
    setup_logging()
    logger = logging.getLogger(__name__)

    engine = create_engine('sqlite:///{}'.format(runs_db_path), echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    rrapi = RRApi(rrapi_url, debug=True)
    dbsApi = DbsApi(url=dbsapi_url)

    days_old_runs_date = datetime.date.fromordinal(datetime.date.today().toordinal() - days_old_runs).strftime(
        "%Y-%m-%d")
    if harvest_all_runs:
        filters['number'] = "> {}".format(first_run_number)
    else:
        filters['startTime'] = "> {}".format(days_old_runs_date)
    recent_runs = []
    try:
        logger.info("Fetching Run Registry records from last {} days".format(days_old_runs))
        recent_runs = rrapi.data(workspace=workspace, columns=columns, table=table, template=template, filter=filters)
    except RRApiError:
        logger.error("Error while querying RR API for {} days old runs".format(days_old_runs), exc_info=True)

    logger.info("Ignoring runs with no runClassName specified")
    runs_with_classname = [r for r in recent_runs if r[u'runClassName']]

    logger.info("Checking if all the runs have start date")
    for run in runs_with_classname:
        if u'startTime' not in run:
            logger.error("Run without a start date: {}. Ignoring.".format(run[u'number']))
    valid_runs = (r for r in runs_with_classname if r[u'startTime'])

    logger.info("Getting {} days old runs form local database".format(days_old_runs))
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
                old_run.run_class_name = run[u'run_class_name']
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
    complete_runs = session.query(RunInfo).filter(RunInfo.stop_time != None,
                                                  RunInfo.start_time > days_old_runs_date).all()
    # TODO #1: test if the date comparison works properly

    t0api = Tier0Api()
    logger.info("Starting creating multiruns...")
    for run in complete_runs:

        logger.debug("Retrieving express config for run {}".format(run.number))
        release = t0api.get_run_info(run.number)
        if not release:
            logger.debug("Express config for run {} is not available".format(run.number))
            continue

        logger.debug("Getting already harvested blocks for run {}".format(run.number))
        harvested_blocks = session.query(RunBlock.block_name).filter(RunBlock.run_number == run.number).all()

        datasets = dbsApi.listDatasets(run_num=run.number, dataset='/*/*/ALCAPROMPT')
        for dataset in datasets:

            files, number_of_events = [], 0

            logger.debug("Getting multirun for the dataset {} for run {}".format(dataset['dataset'], run.number))
            multiruns = session.query(Multirun).filter(Multirun.dataset == dataset['dataset'], Multirun.closed == False,
                                                       Multirun.bfield == run.bfield,
                                                       Multirun.run_class_name == run.run_class_name,
                                                       Multirun.cmssw == release['cmssw'],
                                                       Multirun.scram_arch == release['scram_arch'],
                                                       Multirun.scenario == release['scenario'],
                                                       Multirun.global_tag == release['global_tag']).all()
            # TODO #4 - release should be equal up to 2 digits?

            multirun = None
            for m in multiruns:
                # TODO #7: test it, I am pretty sure it is NOT working properly
                if set(m.workflows) == set(release['workflows']):
                    multirun = m

            if not multirun:
                multirun = Multirun(number_of_events=number_of_events, dataset=dataset['dataset'], bfield=run.bfield,
                                    run_class_name=run.run_class_name, closed=False, cmssw=release['cmssw'],
                                    scram_arch=release['scram_arch'], scenario=release['scenario'],
                                    global_tag=release['global_tag'])
                session.add(multirun)
                # force generation of multirun.id which is accessed later on in this code
                session.flush()
                session.refresh(multirun)
                for workflow in release['workflows']:
                    session.add(Workflow(workflow=workflow, multirun_id=multirun.id))
                logger.info(
                    ("Created new multirun with "
                     "id: {} "
                     "dataset: {} "
                     "bfield: {} "
                     "run classs name: {} "
                     "cmssw: {} "
                     "scram_arch: {} "
                     "scenario: {} "
                     "global_tag: {} "
                     "workflows: {}")
                        .format(
                        multirun.id, multirun.dataset, multirun.bfield, multirun.run_class_name, multirun.cmssw,
                        multirun.scram_arch, multirun.scenario, multirun.global_tag, multirun.workflows))

            logger.debug("Getting files and number of events from new blocks for multirun {}".format(multirun.id))
            blocks = dbsApi.listBlocks(run_num=run.number, dataset=dataset['dataset'])
            for block in blocks:
                if block['block_name'] not in harvested_blocks:
                    run_block = RunBlock(block_name=block['block_name'], run_number=run.number)
                    session.add(run_block)
                    block_files = dbsApi.listFiles(run_num=run.number, block_name=block['block_name'])
                    files.extend(block_files)
                    file_summaries = dbsApi.listFileSummaries(run_num=run.number, block_name=block['block_name'])
                    number_of_events += file_summaries[0]['num_event']

            logger.debug("Adding gathered data to multirun {}".format(multirun.id))
            if number_of_events > 0 and files:
                multirun.number_of_events += number_of_events
                for f in files:
                    multirun_file = Filename(filename=f['logical_file_name'], multirun=multirun.id)
                    session.add(multirun_file)
                if multirun.number_of_events > events_threshold:
                    logger.info(
                        "Multirun {} with {} events ready to be processed".format(multirun.id, number_of_events))
                    multirun.closed = True
                    # TODO #2: inform some other service, that this multirun can be executed

                session.commit()

    session.commit()
