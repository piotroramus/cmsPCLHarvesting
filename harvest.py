import datetime

from dbs.apis.dbsClient import DbsApi

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import logging
from rrapi import RRApi, RRApiError
from logs.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

Base = declarative_base()


# TODO: decouple model from this script
class RunInfo(Base):
    __tablename__ = 'run_info'

    number = Column(Integer, primary_key=True)
    run_class_name = Column(String)
    bfield = Column(Float)
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    # TODO: probably no need for LS
    ls_count = Column(Integer)

    run_blocks = relationship("RunBlock")
    multirun = Column(Integer, ForeignKey('multirun.id'))

    def __repr__(self):
        return "RunInfo(number={}, run_class_name={}, bfield={} start_time={}, end_time={}, ls_count={})".format(
            self.number, self.run_class_name, self.bfield, self.start_time, self.stop_time, self.ls_count)


class RunBlock(Base):
    __tablename__ = 'run_block'

    id = Column(Integer, primary_key=True)
    block_name = Column(String)

    run_number = Column(Integer, ForeignKey('run_info.number'))


class Multirun(Base):
    __tablename__ = 'multirun'

    id = Column(Integer, primary_key=True)
    number_of_events = Column(Integer)
    dataset = Column(String)
    bfield = Column(Float)
    run_class_name = Column(String)
    closed = Column(Boolean)

    run_numbers = relationship("RunInfo")
    filenames = relationship("Filename")


class Filename(Base):
    __tablename__ = 'filename'

    id = Column(Integer, primary_key=True)
    filename = Column(String)

    multirun = Column(Integer, ForeignKey('multirun.id'))


url = "https://cmsweb.cern.ch/dbs/prod/global/DBSReader"
dbsApi = DbsApi(url=url)

db_path = "runs.db"
engine = create_engine('sqlite:///{}'.format(db_path), echo=False)
Base.metadata.create_all(engine, checkfirst=True)

Session = sessionmaker(bind=engine)
session = Session()

rrapi_url = "http://runregistry.web.cern.ch/runregistry/"
rrapi = RRApi(rrapi_url, debug=True)

# just for filling the DB in for the first time
first_run = False

workspace = "GLOBAL"
columns = ['number', 'startTime', 'stopTime', 'runClassName', 'bfield', 'lsCount']
table = "runsummary"
template = 'json'
filters = {}
days_old_runs = 7
days_old_runs_date = datetime.date.fromordinal(datetime.date.today().toordinal() - days_old_runs).strftime("%Y-%m-%d")
if first_run:
    filters['number'] = "> {}".format(230000)
else:
    filters['startTime'] = "> {}".format(days_old_runs_date)
weekly_runs = []
try:
    logger.info("Fetching Run Registry records from last {} days".format(days_old_runs))
    weekly_runs = rrapi.data(workspace=workspace, columns=columns, table=table, template=template, filter=filters)
except RRApiError, e:
    logger.error("Error while querying RR API for {} days old runs".format(days_old_runs), exc_info=True)

logger.info("Ignoring runs with no runClassName specified")
runs_with_classname = [r for r in weekly_runs if r[u'runClassName']]

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
            old_run.ls_count = run[u'lsCount'] if run[u'lsCount'] else 0
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
        ls_count = run[u'lsCount'] if run[u'lsCount'] else 0
        run_info = RunInfo(number=run[u'number'], run_class_name=run[u'runClassName'], bfield=run[u'bfield'],
                           start_time=start, stop_time=stop, ls_count=ls_count)
        session.add(run_info)

    session.commit()

# TODO: extract to some external config
events_limit = 50000
logger.info("Getting complete runs from local database")
complete_runs = session.query(RunInfo).filter(RunInfo.stop_time != None).all()

logger.info("Starting creating multiruns...")
for run in complete_runs:

    logger.debug("Getting already harvested blocks for run {}".format(run.number))
    harvested_blocks = session.query(RunBlock.block_name).filter(RunBlock.run_number == run.number).all()

    datasets = dbsApi.listDatasets(run_num=run.number, dataset='/*/*/ALCAPROMPT')
    for dataset in datasets:

        files, number_of_events = [], 0

        logger.debug("Getting multirun for the dataset {} for run {}".format(dataset['dataset'], run.number))
        multirun = session.query(Multirun).filter(Multirun.dataset == dataset['dataset'], Multirun.closed == False,
                                                  Multirun.bfield == run.bfield,
                                                  Multirun.run_class_name == run.run_class_name).one_or_none()
        if not multirun:
            multirun = Multirun(number_of_events=number_of_events, dataset=dataset['dataset'], bfield=run.bfield,
                                run_class_name=run.run_class_name, closed=False)
            session.add(multirun)
            # force generation of multirun.id which is accessed later on in this code
            session.flush()
            session.refresh(multirun)
            logger.info("Created new multirun {} for dataset {} with bfield {} and run classs name {}".format(
                multirun.id, dataset['dataset'], multirun.bfield, multirun.run_class_name))

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
            if multirun.number_of_events > events_limit:
                logger.info("Multirun {} with {} events ready to be processed".format(multirun.id, number_of_events))
                multirun.closed = True
                # TODO: inform some other service, that this multirun can be executed

            session.commit()

session.commit()
