# CMS PCL MultiRun Harvesting
## Running data discovery

The step looks for a newly available runs and creates multiruns out of them.

```
# setup GRID certificate passing the password as a argument to the script
cd backend/bin
source proxy_cert.sh ${GRID_CERT_PASS_PHRASE}

cd ..
virtualenv env
source env/bin/activate
pip install -r requirements.txt

# example config files can be found in backend/python/config
python python/runDataDiscovery.py --config ${CONFIG_FILE}
```

## Running AlCa Harvesting PCL step

The step takes the multi-runs created by data discovery step and executes AlCa Harvesting step on them.

```
cd backend

virtualenv env
source env/bin/activate
pip install -r requirements.txt

python python/runAlCaHarvesting.py --config $CONFIG_FILE
```

## Running DQM Uploads

Uploads DQM files to DQM GUI produced by previous steps if there are any.

```
cd backend/bin
source proxy_cert.sh ${GRID_CERT_PASS_PHRASE}

cd backend

virtualenv env
source env/bin/activate
pip install -r requirements.txt

python python/runDQMUpload.py --config $CONFIG_FILE

```

## Running payload uploads

Uploads payload to condition database for workflows specified in the config file

```
cd backend

virtualenv env
source env/bin/activate
pip install -r requirements.txt

python python/runPayloadUpload.py $NETRC_FILE --config $CONFIG_FILE
```

The .netrc file which contains credentials necessary for uploading should contain following entry:
```
machine ConditionUploader
        login LOGIN
        password PASSWORD
```

## Running back-end tests

```
cd backend

virtualenv env
source env/bin/activate
pip install -r requirements.txt

cd test
python -m unittest discover
```

## Setting up the web application

The web part is meant to be launched within the keeper environment.
For setting up the keeper environment see: https://cms-conddb-dev.cern.ch/docs/

Before launching the instance, a configuration file needs to be passed:
`export MULTIRUN_CONFIG=/path/to/config.yml`
This should be exactly the same config file that is used for the backend jobs.
It tells the application where to look for the database, EOS storage space and DQM instance dedicated for this deployment.


If everything is set up properly, then the following should start the service:
`/data/services/keeper/keeper.py start cmsDbMultiRunHarvesting`
