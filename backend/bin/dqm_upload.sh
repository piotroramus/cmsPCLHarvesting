#!/usr/bin/env bash

# source common.sh which contains eos function definition
BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${BIN_DIR}/common.sh

DQM_FILENAME="$1"
DQM_FILE_LOCATION="$2"
DQM_UPLOAD_HOST="$3"
MULTIRUN_ID="$4"
PYTHON_DIR="$5"
WORKING_DIR="$6"

echo -e "\nStarting to perfrom DQM upload"
echo "Multi-run ID: ${MULTIRUN_ID}"
echo -e "\n"

# if working directory does not exists create it
if [[ ! -d ${WORKING_DIR} ]]; then
    mkdir ${WORKING_DIR}
fi
cd ${WORKING_DIR}
echo "Working in ${PWD}"

TMP_DIR=upload_tmp
echo "Creating temporary directory ${TMP_DIR}"
mkdir ${TMP_DIR}
cd ${TMP_DIR}

echo "Copying ${DQM_FILE_LOCATION} from EOS"
eos cp --checksum --preserve ${DQM_FILE_LOCATION} ${DQM_FILENAME}
EOS_RC=$?

if [[ ${EOS_RC} -ne 0 ]]; then
    echo "ERROR: Trying to copy ${DQM_FILE_LOCATION} from eos resulted in error"
    echo "EOS command returned ${EOS_RC}"
    exit ${EOS_RC}
fi

echo -e "\nUploading ${DQM_FILENAME} to DQM"
echo -e "Target GUI: ${DQM_UPLOAD_HOST} \n"

python ${PYTHON_DIR}/visDQMUpload.py ${DQM_UPLOAD_HOST} ${DQM_FILENAME}
UPLOAD_RC=$?

echo "DQM exit code: ${UPLOAD_RC}"

echo "Removing temporary directory ${TMP_DIR}"
cd ..
rm -r ${TMP_DIR}

cd ..
rm -r ${WORKING_DIR}

exit ${UPLOAD_RC}