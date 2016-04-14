import datetime

from dbs.apis.dbsClient import DbsApi

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import logging
from rrapi import RRApi, RRApiError
from logs.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

Base = declarative_base()


class RunInfo(Base):
    __tablename__ = 'run_info'

    number = Column(Integer, primary_key=True)
    run_class_name = Column(String)
    bfield = Column(Float)
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    #TODO: probably no need for LS
    ls_count = Column(Integer)

    run_blocks = relationship("RunBlock") #, back_populates="run_info")

    def __repr__(self):
        return "RunInfo(number='%s', run_class_name='%s', bfield='%s' start_time='%s', end_time='%s', ls_count='%s')" % (
            self.number, self.run_class_name, self.bfield, self.start_time, self.stop_time, self.ls_count)


class RunBlock(Base):
    __tablename__ = 'run_blocks'

    id = Column(Integer, primary_key=True)
    block_name = Column(String)

    run_number = Column(Integer, ForeignKey('run_info.number'))


url="https://cmsweb.cern.ch/dbs/prod/global/DBSReader"
dbsApi=DbsApi(url=url)


db_path = "runs.db"
engine = create_engine('sqlite:///%s' % db_path, echo=False)
Base.metadata.create_all(engine, checkfirst=True)

Session = sessionmaker(bind=engine)
session = Session()

rrapi_url = "http://runregistry.web.cern.ch/runregistry/"
api = RRApi(rrapi_url, debug=True)

# just for filling the DB in for the first time
first_run = False

# take runs from last week (as for the starting date)
workspace = "GLOBAL"
columns = ['number', 'startTime', 'stopTime', 'runClassName', 'bfield', 'lsCount']
table = "runsummary"
template = 'json'
filters = {}
week_ago = datetime.date.fromordinal(datetime.date.today().toordinal() - 7).strftime("%Y-%m-%d")
if first_run:
    filters['number'] = "> %s" % 230000
else:
    filters['startTime'] = "> %s" % (week_ago)
weekly_runs = []
try:
    weekly_runs = api.data(workspace=workspace, columns=columns, table=table, template=template, filter=filters)
except RRApiError, e:
    logger.error("Error while querying RR API for week old runs", exc_info=True)

# ignore runs without className
runs_with_classname = [r for r in weekly_runs if r[u'runClassName']]

# ignore runs without a startTime - report an error
for run in runs_with_classname:
    if u'startTime' not in run:
        logger.error("Run without a start date: %s. Ignoring." % run[u'number'])
valid_runs = (r for r in runs_with_classname if r[u'startTime'])

# get week old runs from local DB
local_runs = session.query(RunInfo).filter(RunInfo.start_time > week_ago).all()

complete_runs = [run.number for run in local_runs if run.stop_time]
incomplete_runs = [run.number for run in local_runs if not run.stop_time]

for run in valid_runs:
    if run[u'number'] in complete_runs:
        continue
    if run[u'number'] in incomplete_runs:
        if run[u'stopTime']:
            logger.info("Updating incomplete run %d since it is finished" % run[u'number'])
            start = datetime.datetime.strptime(run[u'startTime'], "%a %d-%m-%y %H:%M:%S")
            stop = datetime.datetime.strptime(run[u'stopTime'], "%a %d-%m-%y %H:%M:%S")
            old_run = session.query(RunInfo).filter(RunInfo.number == run[u'number'])
            old_run.run_class_name = run[u'run_class_name']
            old_run.bfield = run[u'bfield']
            old_run.start_time = start
            old_run.stop_time = stop
            old_run.ls_count = run[u'lsCount'] if run[u'lsCount'] else 0
        else:
            continue
    else:
        logger.info("New run: %d" % run[u'number'])
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


complete_runs = session.query(RunInfo.number).filter(RunInfo.stop_time != None).all()


for run, in complete_runs:
    #get already harvested blocks
    harvested_blocks = session.query(RunBlock.block_name).filter(RunBlock.run_number == run)

    datasets = dbsApi.listDatasets(run_num=run, dataset='/*/*/ALCAPROMPT')
    # TODO: extract workflow out of a dataset and put it somewhere
    for dataset in datasets:
        blocks = dbsApi.listBlocks(run_num=run, dataset=dataset['dataset'])
        for block in blocks:
            if block['block_name'] not in harvested_blocks:
                run_block = RunBlock(block_name=block['block_name'], run_number=run)
                session.add(run_block)

session.commit()

