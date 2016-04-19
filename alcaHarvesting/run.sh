#!/usr/bin/env bash

function die { echo $1: status $2 ;  exit $2; }

function runTest { echo $1 ; python $1 || die "Failure for configuration: $1" $?; }


declare -a arr=("cosmics")
#declare -a arr=("cosmics" "pp" "cosmicsRun2" "cosmicsEra_Run2_25ns" "cosmicsEra_Run2_2016" "ppRun2" "ppRun2B0T" "ppRun2at50ns" "ppEra_Run2_50ns" "ppEra_Run2_25ns" "ppEra_Run2_2016" "pplowpuEra_Run2_2016" "ppEra_Run2_2016_trackingLowPU")

for scenario in "${arr[@]}"
do
     runTest "alcaHarvesting.py --scenario $scenario --lfn /store/whatever --dataset /A/B/C --global-tag GLOBALTAG --workflows=BeamSpotByRun,BeamSpotByLumi,SiStripQuality"
done