# CMS PCL MultiRun Harvesting

In order to be able to use the DBS API Client, before using please do the following:

`source bin/setup.sh`

then enter the certificate pass phrase if needed.

## Running data (new runs) discovery

`python python/runDataDiscovery.py`

It will look for a newly available runs, update local database and create multiruns
out of them.


## Running AlCa Harvesting PCL step

`python python/runAlCaHarvesting.py`

It will take the multiruns created by data discovery step and then try to produce
results of AlCa Harvesting step by using the multiruns as a input data.
