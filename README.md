# CMS PCL MultiRun Harvesting

## Running data (new runs) discovery

`source bin/setup.sh`
`python python/runDataDiscovery.py`

It will look for a newly available runs, update local database and create multiruns
out of them. Sourcing setup file is needed for having an access to DBS API Client.


## Running AlCa Harvesting PCL step

`python python/runAlCaHarvesting.py`

It will take the multiruns created by data discovery step and then try to produce
results of AlCa Harvesting step by using the multiruns as a input data.
