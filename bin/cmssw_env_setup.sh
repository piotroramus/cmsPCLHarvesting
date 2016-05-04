#!/usr/bin/env bash

# sets CMSSW environment up
# should be
# cmssw_env_setup.sh workspace cmsswRelease scramArch

WORKSPACE="$1"
CMSSW_RELEASE="$2"
SCRAM_ARCH="$3"

echo "Creating CMSSW environment in $WORKSPACE"
echo "Release to be used: $CMSSW_RELEASE"
echo "Architecture: $SCRAM_ARCH"

# TODO: consider what to do when the environment already exists
mkdir -p $WORKSPACE
cd $WORKSPACE

export SCRAM_ARCH=$SCRAM_ARCH

# the same as cmsrel $CMSSW_RELEASE
# we cannot use cmsrel because it is an alias not available in current shell
scramv1 project CMSSW $CMSSW_RELEASE