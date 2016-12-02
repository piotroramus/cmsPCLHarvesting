#!/usr/bin/env bash

# sets CMSSW environment up
# script parameters should be placed in properties file which path should be a script argument


# source common.sh which contains definitions of functions like eos, cmsenv and so on
BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${BIN_DIR}/common.sh


function upload_available_files() {
    echo -e "\nUploading available output files to EOS..."
    for FILE in ${FILES_TO_SAVE[@]}; do
        if [[ ! -f ${FILE} ]]; then
            echo "${FILE} does not exists - not proceeding with upload"
        else
            eos cp --preserve --checksum ${FILE} ${EOS_MULTIRUN_WORKSPACE}
            RC=$?
            if [[ ${RC} -ne 0 ]]; then
                # sometimes it is worth retrying upload...
                echo "Waiting 30 seconds and retrying upload..."
                sleep 30
                eos cp --preserve --checksum ${FILE} ${EOS_MULTIRUN_WORKSPACE}
                RC=$?
                if [[ ${RC} -ne 0 ]]; then
                    echo "ERROR: Uploading of ${FILE} to EOS resulted in an error ${RC}"
                    exit ${RC}
                fi
            fi
            echo "Uploaded ${FILE} to ${EOS_MULTIRUN_WORKSPACE}"
        fi
    done
    echo "Updating multi-run eos path"
    python ${PYTHON_DIR_PATH}/updateEosPath.py ${MULTIRUN_ID} ${MULTIRUN_DIR} ${CONFIG_FILE} --oracleSecret ${ORACLE_SECRET_FILE}
}


PROPERTIES_FILE="$1"
if [[ ! -f ${PROPERTIES_FILE} ]]; then
    echo "Shell properties file ${PROPERTIES_FILE} cannot be localized"
    exit 1
fi

source ${PROPERTIES_FILE}

MULTIRUN_PROPS_FILE_PWD=${PWD}/${MULTIRUN_PROPS_FILE}
PROPERTIES_FILE_PWD=${PWD}/${PROPERTIES_FILE}

EOS_MULTIRUN_WORKSPACE=${EOS_WORKSPACE}/${SCRAM_ARCH}/${CMSSW_RELEASE}/${MULTIRUN_DIR}/

DQM_FILE=DQM_V0001_R*__StreamExpress*__*__ALCAPROMPT.root
CONDITIONS_FILE="promptCalibConditions${MULTIRUN_ID}.db"
METADATA_FILE="promptCalibConditions${MULTIRUN_ID}.txt"

# output files to be copied to EOS
FILES_TO_SAVE=(
    ${CONFIG_FILE}
    ${ALCA_CONFIG_FILE}
    ${JOB_REPORT_FILE}
    ${CMS_RUN_OUTPUT}
    ${DQM_FILE}
    ${CONDITIONS_FILE}
    ${METADATA_FILE}
    ${PROPERTIES_FILE}
    ${MULTIRUN_PROPS_FILE}
    )


echo -e "\n"
echo "Multi-run ID: ${MULTIRUN_ID}"
echo "Performing processing in ${PWD}"
echo "Release to be used: ${CMSSW_RELEASE}"
echo "Architecture: ${SCRAM_ARCH}"
echo -e "\n"

source_cmssw_env # defined in common.sh

mkdir ${MULTIRUN_DIR}
cd ${MULTIRUN_DIR}

# python script, which invoked this script, created a file with multirun parameters
# the file was created within python's script working directory so it needs to be moved
mv ${MULTIRUN_PROPS_FILE_PWD} .
mv ${PROPERTIES_FILE_PWD} .

# create cmsRun config for AlCaHarvesting step
python ${PYTHON_DIR_PATH}/configPreparator.py ${MULTIRUN_PROPS_FILE} ${ALCA_CONFIG_FILE} ${JOB_REPORT_FILE}

# update multi-run processing start time
python ${PYTHON_DIR_PATH}/updateProcessingTime.py ${MULTIRUN_ID} ${CONFIG_FILE} start --oracleSecret ${ORACLE_SECRET_FILE}

# run the AlCaHarvesting step
echo "Starting the AlCa Harvesting step..."
cmsRun -j ${JOB_REPORT_FILE} ${ALCA_CONFIG_FILE} 2>&1 | tee ${CMS_RUN_OUTPUT}
CMS_RUN_RESULT=${PIPESTATUS[0]}

# update multi-run processing end time
python ${PYTHON_DIR_PATH}/updateProcessingTime.py ${MULTIRUN_ID} ${CONFIG_FILE} end --oracleSecret ${ORACLE_SECRET_FILE}

# I was just wondering how is it possible, that cmsRun can return something > 255
# while it is not feasible on an unix-based OS
# cmsRun exit codes: https://twiki.cern.ch/twiki/bin/view/CMSPublic/JobExitCodes

echo "cmsRun return code: ${CMS_RUN_RESULT}"
if [[ ${CMS_RUN_RESULT} != 0 ]]; then
    echo "cmsRun returned with non-zero exit code: ${CMS_RUN_RESULT}"
    python ${PYTHON_DIR_PATH}/unprocessedMultirun.py ${MULTIRUN_ID} ${MAX_FAILURE_RETRIES} ${CONFIG_FILE} --oracleSecret ${ORACLE_SECRET_FILE}
    upload_available_files
    exit ${CMS_RUN_RESULT}
fi

# append multirun_id to conditions filename
mv promptCalibConditions.db ${CONDITIONS_FILE}

# create dropbox metadata file
python ${PYTHON_DIR_PATH}/createMetadata.py ${JOB_REPORT_FILE} ${METADATA_FILE} ${MULTIRUN_DIR}

# check if there is exactly one .root (DQM) file
ROOT_FILES_COUNT=$(ls ${DQM_FILE} 2>/dev/null | wc -l)
if [[ ${ROOT_FILES_COUNT} -lt 1 ]]; then
    echo "DQM file is missing!"
    echo "Preparing for retrying the processing..."
    python ${PYTHON_DIR_PATH}/unprocessedMultirun.py ${MULTIRUN_ID} ${MAX_FAILURE_RETRIES} ${CONFIG_FILE} --oracleSecret ${ORACLE_SECRET_FILE}
    upload_available_files
    exit 1
elif [[ ${ROOT_FILES_COUNT} -gt 1 ]]; then
    echo "More than one DQM file!"
    echo "Preparing for retrying the processing..."
    python ${PYTHON_DIR_PATH}/unprocessedMultirun.py ${MULTIRUN_ID} ${MAX_FAILURE_RETRIES} ${CONFIG_FILE} --oracleSecret ${ORACLE_SECRET_FILE}
    upload_available_files
    exit 1
fi


for FILE in ${FILES_TO_SAVE[@]}; do
    if [[ ! -f ${FILE} ]]; then
        echo "Error: ${FILE} does not exists"
        echo "Preparing for retrying the processing..."
        python ${PYTHON_DIR_PATH}/unprocessedMultirun.py ${MULTIRUN_ID} ${MAX_FAILURE_RETRIES} ${CONFIG_FILE} --oracleSecret ${ORACLE_SECRET_FILE}
        upload_available_files
        exit 1
    fi
done

echo "Checking if the payload has been produced..."
PAYLOAD_ROWS=$(sqlite3 ${CONDITIONS_FILE} "select count(*) from TAG")

if [[ ${PAYLOAD_ROWS} -eq 0 ]]; then
    echo "No payload has been produced."
    echo "Multi-run now will go to need_more_data state"
    python ${PYTHON_DIR_PATH}/noPayloadProcessing.py ${MULTIRUN_ID} ${CONFIG_FILE} --oracleSecret ${ORACLE_SECRET_FILE}
    upload_available_files
    exit 0
else
    echo "Payload has been produced"
fi

# mark multirun as processed
python ${PYTHON_DIR_PATH}/markAsProcessed.py ${MULTIRUN_ID} ${CONFIG_FILE} --oracleSecret ${ORACLE_SECRET_FILE}

upload_available_files

echo -e "\nJob finished for multi-run ${MULTIRUN_ID}\n"
