# from alcaHarvesting.envAssembler import dataset_with_runs_range

# dataset = '/StreamExpress/Run2016B-PromptCalibProdSiStripGains-Express-v2/ALCAPROMPT'

# run_range = "123456-123457"
# modified_dataset = dataset_with_runs_range(dataset, run_range)

# print "Dataset: \n\t{}".format(dataset)
# print "Result: \n\t{}".format(modified_dataset)

# from model import Multirun

# multirun = Multirun(number_of_events=0, dataset="/A/B/C",
#                     bfield=3.8, run_class_name="Cosmics",
#                     cmssw="808", scram_arch="530",
#                     scenario="Scenario", global_tag="GT",
#                     retries=0, state_id=1)

# print multirun
#
# from rrapi.rrapi_v3 import RRApi
# import datetime
#
# URL = "http://runregistry.web.cern.ch/runregistry/"
#
# api = RRApi(URL, debug=True)
#
# days_old_runs_date = datetime.date \
#     .fromordinal(datetime.date.today().toordinal() - 2) \
#     .strftime("%Y-%m-%d")
#
# workflow_run_classes = dict()
# workflow_run_classes['PromptCalibProd'] = ['Collisions15', 'Collisions16']
# workflow_run_classes['PromptCalibProdSiStrip'] = ['Collisions15', 'Collisions16']
# workflow_run_classes['PromptCalibProdSiStripGains'] = ['Collisions15', 'Collisions16']
# workflow_run_classes['PromptCalibProdSiPixelAli'] = ['Collisions15', 'Collisions16']
# workflow_run_classes['PromptCalibProdSiStripGainsAfterAbortGap'] = ['Collisions16']
#
# run_class_names = set()
# for workflow_list in workflow_run_classes.itervalues():
#     for workflow in workflow_list:
#         run_class_names.add(workflow)
#
# filters = dict()
# filters['startTime'] = "> {}".format(days_old_runs_date)
# filters['runClassName'] = "= {}".format(' or = '.join(run_class_names))
#
# print filters['runClassName']
#
# workspace = 'GLOBAL'
# columns = ['number', 'startTime', 'runClassName', 'bfield']
# table = 'runsummary'
# template = 'json'
#
# recent_runs = api.data(workspace=workspace, columns=columns, table=table,
#                        template=template, filter=filters)
#
# for run in recent_runs:
#     print run

# from rrapi.rrapi_v4 import RhApi

# url='http://runregistry.web.cern.ch/runregistry/'
# url='http://vocms00169:2113'
# rrapi = RhApi(url, debug=False)  # TODO: change to False

# import datetime
# days_old_runs_date = datetime.date \
#     .fromordinal(datetime.date.today().toordinal() - 3) \
    # .strftime("%Y-%m-%d")

# print days_old_runs_date

# run_class_names = {'Collisions15', 'Collisions16'}
# filters = "where r.starttime > TO_DATE('{}', 'YYYY-MM-DD')".format(days_old_runs_date)
# filters += " and (r.run_class_name = {})".format(" or r.run_class_name = ".join("'" + cn + "'" for cn in run_class_names))
# query = "select r.runnumber, r.run_class_name, r.starttime, r.bfield from runreg_global.runs r {}".format(filters)
# filters += " and (r.run_class_name = 'Collisions15' or r.run_class_name = 'Collisions16')".format('Collisions16')
# print filters

# import sys
# sys.exit(0)

# qid = rrapi.qid(q)
# data = rrapi.data(qid, form='application/json2')
# data = rrapi.json2(query)
# print data

# q = "select r.runnumber, r.run_class_name, r.starttime, r.bfield from runreg_global.runs r where r.starttime > 2016-07-10"
# q = "select r.runnumber, r.run_class_name, r.starttime, r.bfield from runreg_global.runs r where r.starttime > TO_DATE('2016-07-10','YYYY-MM-DD')"


from t0wmadatasvcApi.t0wmadatasvcApi import Tier0Api

tapi = Tier0Api()
print tapi.firstconditionsaferun()