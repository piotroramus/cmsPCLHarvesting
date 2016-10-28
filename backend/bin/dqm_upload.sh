#!/usr/bin/env bash

function eos() {
   /afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select "$@"
}


DQM_FILENAME="$1"
DQM_FILE_LOCATION="$2"
DQM_UPLOAD_HOST="$3"
MULTIRUN_ID="$4"
PYTHON_DIR="$5"

# TODO: this is done by Jenkins now before running the job - consider what to do with it
#echo -e "\nGoing to refresh GRID certificate..."
#SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#source $SCRIPT_DIR/proxy_cert.sh

echo -e "\n Starting to perfrom DQM upload"
echo "Multi-run ID: ${MULTIRUN_ID}"
echo -e "\n"

TMP_DIR=upload_tmp
echo "Creating temporary directory $TMP_DIR"
mkdir ${TMP_DIR}
cd ${TMP_DIR}

echo "Copying $DQM_FILE_LOCATION from EOS"
eos cp --checksum --preserve $DQM_FILE_LOCATION $DQM_FILENAME
EOS_RC=$?

if [ ${EOS_RC} -ne 0 ]; then
    echo "ERROR: Trying to copy $DQM_FILE_LOCATION from eos resulted in error"
    echo "EOS command returned $EOS_RC"
    exit ${EOS_RC}
fi

echo -e "\nUploading $DQM_FILENAME to DQM"
echo -e "Target GUI: ${DQM_UPLOAD_HOST} \n"

python ${PYTHON_DIR}/visDQMUpload.py $DQM_UPLOAD_HOST $DQM_FILENAME
UPLOAD_RC=$?

echo "DQM exit code: $UPLOAD_RC"

echo "Removing temporary directory $TMP_DIR"
cd ..
rm -r ${TMP_DIR}

exit ${UPLOAD_RC}