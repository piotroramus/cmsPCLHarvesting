#!/usr/bin/env bash

# magic to check if the script was sourced
if [[ ! ${0##*/} == -* ]]; then

    echo "This script should be sourced rather than executed in different shell"

else

    echo "Generating new proxy certificate..."
    voms-proxy-init -rfc -voms cms
    export X509_USER_PROXY=$(voms-proxy-info --path)


    # TODO: first check if user has an access to /cvmfs/cms.cern.ch - if not raise an error message

    source /cvmfs/cms.cern.ch/crab3/crab.sh
fi