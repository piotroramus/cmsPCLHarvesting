#!/usr/bin/env bash

function eos() {
   /afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select "$@"
}

function cmsenv() {
    eval `scramv1 runtime -sh`
}

EOS_PATH="$1"
CONDITIONS_FILENAME="$2"
METADATA_FILENAME="$3"
SCRAM_ARCH="$4"
CMSSW_RELEASE="$5"


# check for existence of ~/.netrc file
if [ ! -f ~/.netrc ]; then
    echo "./netrc file does not exists!"
    echo "It should contain user credentials for connecting to Dropbox in following format"
    echo "machine ConditionUploader login __login__ password __password__"
    exit 10
fi

TMP_DIR=upload_tmp
echo "Creating temporary directory $TMP_DIR"
mkdir ${TMP_DIR}
cd ${TMP_DIR}

CONDITIONS_FILE_LOCATION=$EOS_PATH/$CONDITIONS_FILENAME
METADATA_FILE_LOCATION=$EOS_PATH/$METADATA_FILENAME

echo "Copying $CONDITIONS_FILE_LOCATION from EOS"
eos cp $CONDITIONS_FILE_LOCATION $CONDITIONS_FILENAME
EOS_RC=$?

if [ EOS_RC -ne 0 ]; then
    echo "ERROR: Trying to copy $CONDITIONS_FILE_LOCATION from eos resulted in error"
    echo "EOS command returned $EOS_RC"
    exit $EOS_RC
fi


echo "Copying $METADATA_FILE_LOCATION from EOS"
eos cp $METADATA_FILE_LOCATION $METADATA_FILENAME
EOS_RC=$?

if [ EOS_RC -ne 0 ]; then
    echo "ERROR: Trying to copy $METADATA_FILE_LOCATION from eos resulted in error"
    echo "EOS command returned $EOS_RC"
    exit $EOS_RC
fi


# source CMSSW environment for access to uploadConditions.py
pushd .

# get CMSSW_RELEASE location
CMSSW_RELEASE_DIR=$(
                    scram -a $SCRAM_ARCH list -c CMSSW $CMSSW_RELEASE |
                    awk -v pattern="^$CMSSW_RELEASE$" '$2 ~ pattern {print $3}'
                    )

echo "Sourcing environment from $CMSSW_RELEASE_DIR/src"
cd $CMSSW_RELEASE_DIR/src
cmsenv

popd


echo "Uploading $CONDITIONS_FILENAME to Dropbox"
uploadConditions.py $CONDITIONS_FILENAME
UPLOAD_RC=$?

echo "Upload exit code: $UPLOAD_RC"

echo "Removing temporary directory $TMP_DIR"
cd ..
rm -r ${TMP_DIR}

exit ${UPLOAD_RC}