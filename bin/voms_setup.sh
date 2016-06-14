#!/usr/bin/env bash


# magic to check if the script was sourced
if [[ ! ${0##*/} == -* ]]; then
    echo "This script should be sourced rather than executed in different shell"
    exit 1
fi

echo "Generating new proxy certificate..."

VOMS_PASS_PHRASE_FILE="voms.pwd"
if [ ! -f $VOMS_PASS_PHRASE_FILE ]; then
    echo "Error: $VOMS_PASS_PHRASE_FILE file is missing!"
    exit 1
fi

source $VOMS_PASS_PHRASE_FILE
if [ -z ${GRID_PASS_PHRASE+x} ]; then
    echo "Error: GRID_PASS_PHRASE not set in $VOMS_PASS_PHRASE_FILE!"
    exit 1
fi

echo $GRID_PASS_PHRASE | voms-proxy-init -rfc -voms cms -pwstdin
rc=$?
if [ $rc -eq 3 ]; then
    echo "Error: Wrong passphrase for GRID certificate!"
    exit $rc
fi

export X509_USER_PROXY=$(voms-proxy-info --path)

if [ ! -d "/cvmfs/cms.cern.ch" ]; then
    echo "Error: User $(whoami) does not have access to /cvmfs/cms.cern.ch space"
    echo "Please grant the access first"
    exit 1
fi

source /cvmfs/cms.cern.ch/crab3/crab.sh
