#!/bin/bash

# save the commands to a file and then send it to an interactive queue
# logging into queue first and then executing commands will not work!
# (connection will be terminated just after it has been established)
echo '

cd ${WORKSPACE}/backend/bin
source proxy_cert.sh ${GRID_CERT_PASS_PHRASE}

# there is no python2.7 on CAF machines
# hence there is a need for a python2.7 on cvmfs
# it is significantly faster to source needed packages than install it
# (installing cx-Oracle is very tricky and sometimes impossible)
# only SQLAlchemy needs to be installed since it is too old on cvmfs
CVMFS_TOOLS=/cvmfs/cms.cern.ch/slc6_amd64_gcc530/external
source ${CVMFS_TOOLS}/python/2.7.11-giojec3/etc/profile.d/init.sh
source ${CVMFS_TOOLS}/oracle/12.1.0.2.0/etc/profile.d/init.sh
source ${CVMFS_TOOLS}/py2-cx-oracle/5.2.1-giojec3/etc/profile.d/init.sh
source ${CVMFS_TOOLS}/py2-PyYAML/3.11-giojec3/etc/profile.d/init.sh
source ${CVMFS_TOOLS}/py2-requests/2.5.1-giojec3/etc/profile.d/init.sh
source ${CVMFS_TOOLS}/py2-cjson/1.0.5-giojec3/etc/profile.d/init.sh

cd ${WORKSPACE}/backend
virtualenv -p ${CVMFS_TOOLS}/python/2.7.11-giojec3/bin/python env
source env/bin/activate
pip install "SQLAlchemy==1.0.12"


python python/runDQMUpload.py --config ${CONFIG_FILE} --jenkinsBuildUrl ${BUILD_URL} --oracleSecret ${ORACLE_SECRET}

' > script.sh

# run script as an interactive job
bsub -Is -q cmsinter /bin/bash -l < script.sh
