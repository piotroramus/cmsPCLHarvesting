#!/usr/bin/env bash

# sets CMSSW environment up
# script parameters should be placed in properties file which path should be a script argument

function cmsenv() {
    eval `scramv1 runtime -sh`
}

function eos() {
   /afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select "$@"
}

function upload_available_files() {
    echo -e "\nUploading available output files to EOS..."
    for file in ${FILES_TO_SAVE[@]}; do
        if [ ! -f $file ]; then
            echo "$file does not exists - not proceeding with upload"
        else
            eos cp $file $EOS_MULTIRUN_WORKSPACE
            echo "Uploaded $file to $EOS_MULTIRUN_WORKSPACE"
        fi
    done
    echo "Updating multi-run eos path"
    python $PYTHON_DIR_PATH/updateEosPath.py $MULTIRUN_ID $DB_PATH $MULTIRUN_DIR
}


PROPERTIES_FILE="$1"
if [ ! -f $PROPERTIES_FILE ]; then
    echo "Shell properties file $PROPERTIES_FILE cannot be localized"
    exit 1
fi

source $PROPERTIES_FILE

MULTIRUN_PROPS_FILE_PWD=$PWD/$MULTIRUN_PROPS_FILE
PROPERTIES_FILE_PWD=$PWD/$PROPERTIES_FILE


DQM_FILE=DQM_V0001_R*__StreamExpress__*__ALCAPROMPT.root
CONDITIONS_FILE="promptCalibConditions$MULTIRUN_ID.db"
METADATA_FILE="promptCalibConditions$MULTIRUN_ID.txt"

# output files to be copied to EOS
FILES_TO_SAVE=(
    $ALCA_CONFIG_FILE
    $JOB_REPORT_FILE
    $CMS_RUN_OUTPUT
    $DQM_FILE
    $CONDITIONS_FILE
    $METADATA_FILE
    multirunProperties*.txt
    shellProperties*.txt
    )


echo "Multi-run ID: $MULTIRUN_ID"
echo "Creating $CMSSW_RELEASE environment in $WORKSPACE"
echo "Release to be used: $CMSSW_RELEASE"
echo "Architecture: $SCRAM_ARCH"


mkdir -p $WORKSPACE/$CMSSW_RELEASE


# get CMSSW_RELEASE location
CMSSW_RELEASE_DIR=$(
                    scram -a $SCRAM_ARCH list -c CMSSW $CMSSW_RELEASE |
                    awk -v pattern="^$CMSSW_RELEASE$" '$2 ~ pattern {print $3}'
                    )

echo "Sourcing environment from $CMSSW_RELEASE_DIR/src"
cd $CMSSW_RELEASE_DIR/src
cmsenv

cd $WORKSPACE/$CMSSW_RELEASE


MULTIRUN_DIR=$MULTIRUN_ID
if [ -d "$MULTIRUN_ID" ]; then
    # Create new folder for multirun, named multirunId_YYYY-mm-dd_HHMM
    # For example 34_2016-05-24_1703
    DATE=`date +%Y-%m-%d_%H%M`
    MULTIRUN_DIR="${MULTIRUN_ID}_${DATE}"
fi

EOS_MULTIRUN_WORKSPACE=$EOS_WORKSPACE/$SCRAM_ARCH/$CMSSW_RELEASE/$MULTIRUN_DIR/

mkdir $MULTIRUN_DIR
cd $MULTIRUN_DIR

# python script, which invoked this script, created a file with multirun parameters
# the file was created within python's script working directory so it needs to be moved
mv $MULTIRUN_PROPS_FILE_PWD .
mv $PROPERTIES_FILE_PWD .

# create cmsRun config for AlCaHarvesting step
python $PYTHON_DIR_PATH/configPreparator.py $MULTIRUN_PROPS_FILE $ALCA_CONFIG_FILE $JOB_REPORT_FILE

# run the AlCaHarvesting step
cmsRun -j FrameworkJobReport.xml alcaConfig.py 2>&1 | tee $CMS_RUN_OUTPUT
CMS_RUN_RESULT=${PIPESTATUS[0]}

# I was just wondering how is it possible, that cmsRun can return something > 255
# while it is not feasible on an unix-based OS
# cmsRun exit codes: https://twiki.cern.ch/twiki/bin/view/CMSPublic/JobExitCodes

echo "cmsRun return code: $CMS_RUN_RESULT"
if [[ $CMS_RUN_RESULT != 0 ]]; then
    echo "cmsRun returned with non-zero exit code: $CMS_RUN_RESULT"
    upload_available_files
    python $PYTHON_DIR_PATH/unprocessedMultirun.py $MULTIRUN_ID $DB_PATH $MAX_RETRIES
    exit $CMS_RUN_RESULT
fi

# append multirun_id to conditions file
mv promptCalibConditions.db $CONDITIONS_FILE

# create dropbox metadata file
python $PYTHON_DIR_PATH/createMetadata.py $JOB_REPORT_FILE $METADATA_FILE $MULTIRUN_DIR

# check if there is exactly one .root (DQM) file
root_files_count=$(ls $DQM_FILE 2>/dev/null | wc -l)
if [ $root_files_count -lt 1 ]; then
    echo "DQM file is missing!"
    upload_available_files
    echo "Preparing for retrying the processing..."
    python $PYTHON_DIR_PATH/unprocessedMultirun.py $MULTIRUN_ID $DB_PATH $MAX_RETRIES
    exit 1
elif [ $root_files_count -gt 1 ]; then
    echo "More than one DQM file!"
    upload_available_files
    echo "Preparing for retrying the processing..."
    python $PYTHON_DIR_PATH/unprocessedMultirun.py $MULTIRUN_ID $DB_PATH $MAX_RETRIES
    exit 1
fi


for file in ${FILES_TO_SAVE[@]}; do
    if [ ! -f $file ]; then
        echo "Error: $file does not exists"
        upload_available_files
        echo "Preparing for retrying the processing..."
        python $PYTHON_DIR_PATH/unprocessedMultirun.py $MULTIRUN_ID $DB_PATH $MAX_RETRIES
        exit 1
    fi
done

upload_available_files

# mark multirun as processed
python $PYTHON_DIR_PATH/markAsProcessed.py $MULTIRUN_ID $DB_PATH

echo -e "\nJob finished for multi-run $MULTIRUN_ID\n"