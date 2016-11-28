#!/usr/bin/env bash

function upload() {

    echo -e "\nStarting to perform the Dropbox upload"
    echo "Multi-run ID: ${MULTIRUN_ID}"
    echo -e "\n"

    TMP_DIR=upload_tmp
    echo "Creating temporary directory ${TMP_DIR}"
    mkdir ${TMP_DIR}
    cd ${TMP_DIR}

    CONDITIONS_FILE_LOCATION=${EOS_PATH}/${CONDITIONS_FILENAME}
    METADATA_FILE_LOCATION=${EOS_PATH}/${METADATA_FILENAME}

    echo "Copying ${CONDITIONS_FILE_LOCATION} from EOS"
    eos cp --preserve --checksum ${CONDITIONS_FILE_LOCATION} ${CONDITIONS_FILENAME}
    EOS_RC=$?

    if [ ${EOS_RC} -ne 0 ]; then
        echo "ERROR: Trying to copy ${CONDITIONS_FILE_LOCATION} from eos resulted in error"
        echo "EOS command returned ${EOS_RC}"
        return ${EOS_RC}
    fi


    echo "Copying ${METADATA_FILE_LOCATION} from EOS"
    eos cp --preserve --checksum ${METADATA_FILE_LOCATION} ${METADATA_FILENAME}
    EOS_RC=$?

    if [ ${EOS_RC} -ne 0 ]; then
        echo "ERROR: Trying to copy ${METADATA_FILE_LOCATION} from eos resulted in error"
        echo "EOS command returned ${EOS_RC}"
        return ${EOS_RC}
    fi

    # source CMSSW environment for access to uploadConditions.py
    source_cmssw_env # defined in common.sh

    echo "Uploading ${CONDITIONS_FILENAME} to Dropbox"
    uploadConditions.py ${CONDITIONS_FILENAME} 2>&1 | tee ${LOG_FILE}
    UPLOAD_RC=${PIPESTATUS[0]}

    echo "Upload exit code: ${UPLOAD_RC}"

    echo "Removing temporary directory ${TMP_DIR}"
    cd ..
    rm -r ${TMP_DIR}

    return ${UPLOAD_RC}
}


BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${BIN_DIR}/common.sh


NETRC_FILE="$1"
EOS_PATH="$2"
CONDITIONS_FILENAME="$3"
METADATA_FILENAME="$4"
SCRAM_ARCH="$5"
CMSSW_RELEASE="$6"
MULTIRUN_ID="$7"
LOG_FILE="$8"


NETRC_BACKUP=${HOME}/.netrcbackup
ORIG_NETRC=${HOME}/.netrc

if [ -f ${ORIG_NETRC} ]; then
	echo "${ORIG_NETRC} file exists, the backup will be made and after processing it will be restored"
    cp ${ORIG_NETRC} ${NETRC_BACKUP}
    echo "Temporarily swapping the file..."
    cp ${NETRC_FILE} ${ORIG_NETRC}

    upload
    UPLOAD_RESULT=$?

    echo "Switching back to the original .netrc file"
    cp ${NETRC_BACKUP} ${ORIG_NETRC}
    rm ${NETRC_BACKUP}

    exit ${UPLOAD_RESULT}
else
	echo ".netrc file does not exists, for the time of upload a temporary one will be provided"
	cp ${NETRC_FILE} ${ORIG_NETRC}

    upload
    UPLOAD_RESULT=$?

    rm ${ORIG_NETRC}
    exit ${UPLOAD_RESULT}
fi
