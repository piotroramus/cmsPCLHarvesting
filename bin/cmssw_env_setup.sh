#!/usr/bin/env bash

# sets CMSSW environment up
# should be called as the following:
# cmssw_env_setup.sh workspace cmsswRelease scramArch multirun_id multirun_params_filename path_to_python_scripts dqmgui_dir dqm_upload_host

WORKSPACE="$1"
CMSSW_RELEASE="$2"
SCRAM_ARCH="$3"
MULTIRUN_ID="$4"
PARAMS_FILE="$5"
PYTHON_DIR_PATH="$6"
DQMGUI_DIR="$7"
DQM_UPLOAD_HOST="$8"

PARAMS_FILE_PWD=$PWD/$PARAMS_FILE

echo "Creating CMSSW environment in $WORKSPACE"
echo "Release to be used: $CMSSW_RELEASE"
echo "Architecture: $SCRAM_ARCH"


mkdir -p $WORKSPACE
cd $WORKSPACE

# if given CMSSW environment does not exists for the given architecture - create it
if [ ! -d "$CMSSW_RELEASE" ]; then
    export SCRAM_ARCH=$SCRAM_ARCH
    # the same as cmsrel $CMSSW_RELEASE
    scramv1 project CMSSW $CMSSW_RELEASE
fi


cd $CMSSW_RELEASE/src
eval `scramv1 runtime -sh`

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
mv $PARAMS_FILE_PWD .

# create cmsRun config for AlCaHarvesting step
python $PYTHON_DIR_PATH/configPreparator.py $PARAMS_FILE

# run the AlCaHarvesting step
cmsRun -j FrameworkJobReport.xml alcaConfig.py 2>&1 | tee jobOutput.txt

# handle results of the job
python $PYTHON_DIR_PATH/resultsHandler.py

# upload DQM file
# check if there is exactly one .root file
root_files_count=$(ls *.root 2>/dev/null | wc -l)
if [ $root_files_count -lt 1 ]; then
    echo "DQM file is missing!"
    echo "DQM file upload failed."
elif [ $root_files_count -gt 1 ]; then
    echo "More than one DQM file!"
    echo "DQM file upload failed."
else
    source $DQMGUI_DIR/current/apps/dqmgui/128/etc/profile.d/env.sh
    visDQMUpload $DQM_UPLOAD_HOST $(ls *.root)
fi