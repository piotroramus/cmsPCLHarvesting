#!/usr/bin/env bash

function cmsenv() {
    eval `scramv1 runtime -sh`
}

function eos() {
   /afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select "$@"
}

function source_cmssw_env() {

    pushd .

    # get CMSSW_RELEASE directory location for particular SCRAM_ARCH and CMSSW_RELEASE
    CMSSW_RELEASE_DIR=$(
                        scram -a ${SCRAM_ARCH} list -c CMSSW ${CMSSW_RELEASE} |
                        awk -v pattern="^${CMSSW_RELEASE}$" '$2 ~ pattern {print $3}'
                        )

    echo -e "Sourcing environment from ${CMSSW_RELEASE_DIR}/src \n"
    cd ${CMSSW_RELEASE_DIR}/src
    cmsenv

    popd
}
