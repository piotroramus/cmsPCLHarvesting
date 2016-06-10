dbsapi_url = "https://cmsweb.cern.ch/dbs/prod/global/DBSReader"
rrapi_url = "http://runregistry.web.cern.ch/runregistry/"

# path to database containing all the harvesting information
runs_db_path = "/afs/cern.ch/work/p/poramus/database/database.db"

# where to setup environments for AlCaHarvesting
workspace_path = "/afs/cern.ch/work/p/poramus/cmsenvs"

# location of `current` DQM GUI directory
dqm_current = "/datadqm/testGui"

# where to upload resultant DQM file
dqm_upload_host = "http://piotri.cern.ch:8060/dqm/dev"

# how far in the past should we look for new runs
days_old_runs = 7

# in case we want to get all the runs (eg. for the first time)
harvest_all_runs = False
first_run_number = 230000  # respects all 2015 and following runs

# things to search for in the Run Registry
workspace = "GLOBAL"
columns = ['number', 'startTime', 'stopTime', 'runClassName', 'bfield']
table = "runsummary"
template = 'json'
filters = {}

# how many events multirun should contain to be qualified as ready to start
events_threshold = 100000

# only specified runClasses will be processed while using the particular workflow
workflow_run_classes = {
    'PromptCalibProd': ['Collisions15', 'Collisions16'],
    'PromptCalibProdSiStrip': ['Collisions15', 'Collisions16'],
    'PromptCalibProdSiStripGains': ['Collisions15', 'Collisions16'],
    'PromptCalibProdSiPixelAli': ['Collisions15', 'Collisions16']
}
