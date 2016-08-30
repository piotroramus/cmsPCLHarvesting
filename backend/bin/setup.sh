#!/usr/bin/env bash


echo "Generating new proxy certificate..."

CREDENTIALS_FILE="$HOME/.credentials"
if [ ! -f $CREDENTIALS_FILE ]; then
    echo "Error: $CREDENTIALS_FILE file is missing!"
    exit 1
fi

source $CREDENTIALS_FILE
if [ -z ${GRID_PASS_PHRASE+x} ]; then
    echo "Error: GRID_PASS_PHRASE not set in $CREDENTIALS_FILE!"
    exit 1
fi

echo $GRID_PASS_PHRASE | voms-proxy-init -rfc -voms cms -pwstdin
rc=$?
if [ $rc -eq 3 ]; then
    echo "Error: Wrong passphrase for GRID certificate!"
    exit $rc
fi

export X509_USER_PROXY=$(voms-proxy-info --path)
