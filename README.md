# CMS PCL MultiRun Harvesting

## Running data (new runs) discovery

### Get access to DBS python client

`source bin/setup.sh`

### Setup python virtual environment

`virtualenv env`
`source env/bin/activate`
`pip install -r requirements.txt`


### Run data discovery

`python python/runDataDiscovery.py`

It will look for a newly available runs, update local database and create multiruns out of them. 
One important thing here is that you should follow these steps exactly in this order.
This is caused by the fact than libraries linked by `setup.sh` should be shadowed be the ones from requirements file.


## Running AlCa Harvesting PCL step

### Setup python virtual environment (if not done yet)

`virtualenv env`
`source env/bin/activate`
`pip install -r requirements.txt`

###  Run AlCa Harvesting

`python python/runAlCaHarvesting.py`

It will take the multiruns created by data discovery step and then try to produce
results of AlCa Harvesting step by using the multiruns as a input data.
