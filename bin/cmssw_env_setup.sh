#!/usr/bin/env bash

# sets CMSSW environment up
# script parameters should be placed in properties file which path should be a script argument

# TODO: check for properties file existence and so on

PROPERTIES_FILE="$1"
source $PROPERTIES_FILE

MULTIRUN_PROPS_FILE_PWD=$PWD/$MULTIRUN_PROPS_FILE
PROPERTIES_FILE_PWD=$PWD/$PROPERTIES_FILE

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
eval `scramv1 runtime -sh`

cd $WORKSPACE/$CMSSW_RELEASE


MULTIRUN_DIR=$MULTIRUN_ID
if [ -d "$MULTIRUN_ID" ]; then
    # Create new folder for multirun, named multirunId_YYYY-mm-dd_HHMM
    # For example 34_2016-05-24_1703
    DATE=`date +%Y-%m-%d_%H%M`
    MULTIRUN_DIR="${MULTIRUN_ID}_${DATE}"
fi

mkdir $MULTIRUN_DIR
cd $MULTIRUN_DIR

# python script, which invoked this script, created a file with multirun parameters
# the file was created within python's script working directory so it needs to be moved
mv $MULTIRUN_PROPS_FILE_PWD .
mv $PROPERTIES_FILE_PWD .

# create cmsRun config for AlCaHarvesting step
python $PYTHON_DIR_PATH/configPreparator.py $MULTIRUN_PROPS_FILE

# run the AlCaHarvesting step
cmsRun -j FrameworkJobReport.xml alcaConfig.py 2>&1 | tee jobOutput.txt
CMS_RUN_RESULT=$?

if [[ $CMS_RUN_RESULT != 0 ]]; then
    echo "cmsRun returned with non-zero exit code: $CMS_RUN_RESULT"
    python $PYTHON_DIR_PATH/unprocessedMultirun.py $MULTIRUN_ID $DB_PATH $MAX_RETRIES
    exit $CMS_RUN_RESULT
fi


# handle results of the job
python $PYTHON_DIR_PATH/resultsHandler.py $MULTIRUN_ID $DB_PATH

# upload DQM file
# check if there is exactly one .root file
root_files_count=$(ls *.root 2>/dev/null | wc -l)
if [ $root_files_count -lt 1 ]; then
    # TODO: retry multirun processing?
    echo "DQM file is missing!"
    echo "DQM file upload failed."
elif [ $root_files_count -gt 1 ]; then
    echo "More than one DQM file!"
    echo "DQM file upload failed."
else
    source $DQM_GUI_DIR/current/apps/dqmgui/128/etc/profile.d/env.sh
    visDQMUpload $DQM_UPLOAD_HOST $(ls *.root)
fi

# TODO: if this job returns 0 then DataDiscovery project should be triggered ?