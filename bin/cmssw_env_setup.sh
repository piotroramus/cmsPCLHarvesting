#!/usr/bin/env bash

# sets CMSSW environment up
# should be
# cmssw_env_setup.sh workspace cmsswRelease scramArch multirun_id filename

WORKSPACE="$1"
CMSSW_RELEASE="$2"
SCRAM_ARCH="$3"
MULTIRUN_ID="$4"
PARAMS_FILE="$5"

PARAMS_FILE_PWD=$PWD/$PARAMS_FILE

echo "Creating CMSSW environment in $WORKSPACE"
echo "Release to be used: $CMSSW_RELEASE"
echo "Architecture: $SCRAM_ARCH"

# TODO: consider what to do when the environment already exists
mkdir -p $WORKSPACE
cd $WORKSPACE

# TODO: check if env already exists - if yes, then skip creating it
export SCRAM_ARCH=$SCRAM_ARCH

# the same as cmsrel $CMSSW_RELEASE
# we cannot use cmsrel because it is an alias not available in current shell
scramv1 project CMSSW $CMSSW_RELEASE

cd $CMSSW_RELEASE/src
eval `scramv1 runtime -sh`

# TODO: check if multirun dir exists - if yes, then probably we want to create something like id_date or whatever
mkdir $MULTIRUN_ID
cd $MULTIRUN_ID

mv $PARAMS_FILE_PWD .

python /afs/cern.ch/user/p/poramus/shared/cmsPCLHarvesting/python/configPreparator.py $PARAMS_FILE

cmsRun -j FrameworkJobReport.xml alcaConfig.py 2>&1 | tee jobOutput.txt
