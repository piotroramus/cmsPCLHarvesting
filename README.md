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