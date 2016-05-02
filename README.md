# CMS PCL MultiRun Harvesting

In order to be able to use the DBS API Client, before using please do the following:

`source setup.sh`

then enter the certificate pass phrase if needed.

## For running data (new runs) discovery execute

`python runDataDiscovery.py`

It will look for a newly available runs, update local database and create multiruns
out of them.


## For running AlCa Harvesting PCL step execute

`python runAlCaHarvesting.py`

It will take the multiruns created by data discovery step and then try to produce
results of AlCa Harvesting step by using the multiruns as a input data.
