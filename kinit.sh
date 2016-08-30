#!/usr/bin/env bash

while [ 1 ]; do
    grep password $HOME/.credentials | cut -f2 -d: | kinit
    ##klist  | mailx -s "kinit for pdmvserv" pdmvserv@cern.ch
    ##aklog
    sleep 3600
done