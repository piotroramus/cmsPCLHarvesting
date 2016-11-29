#!/usr/bin/env bash

if [[ "$#" -ne 1 ]]; then
    echo "Script usage: source ${BASH_SOURCE} GRID_CERT_PASS_PHRASE"
    exit 1
fi

GRID_CERT_PASS_PHRASE="$1"

echo "Generating new proxy certificate..."

echo ${GRID_CERT_PASS_PHRASE} | voms-proxy-init -rfc -voms cms -pwstdin
RC=$?
if [[ ${RC} -eq 3 ]]; then
    echo "Error: Wrong passphrase for GRID certificate!"
    exit ${RC}
fi

export X509_USER_PROXY=$(voms-proxy-info --path)
