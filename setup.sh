#!/usr/bin/env bash

# TODO: is there any way to check if script was sourced or if it was run?
#       basically this script should be sourced

echo "Generating new proxy certificate..."
voms-proxy-init -rfc -voms cms
export X509_USER_PROXY=$(voms-proxy-info --path)


# TODO: first check if user has an access to /cvmfs/cms.cern.ch - if not raise an error message
source /cvmfs/cms.cern.ch/crab3/crab.sh
