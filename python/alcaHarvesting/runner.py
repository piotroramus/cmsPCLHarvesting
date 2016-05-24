import argparse
import logging
import json
import subprocess

import config

from logs.logger import setup_logging
from model import Base, Multirun

setup_logging()
logger = logging.getLogger(__name__)

# change this to https://github.com/cms-sw/cmssw/blob/CMSSW_8_1_X/Configuration/AlCa/python/autoPCL.py
mapping = {
    'PromptCalibProd': ['BeamSpotByRun', 'BeamSpotByLumi', 'SiStripQuality'],
    'PromptCalibProdSiStrip': ['SiStripQuality'],
    'PromptCalibProdSiStripGains': ['SiStripGains'],
    'PromptCalibProdSiPixelAli': ['SiPixelAli']
}

import re
def extract_workflow(dataset):
    pattern = r'/(?P<primary_dataset>.*)/(?P<acquisition_era>.*?)-(?P<workflow>.*?)-(?P<version>.*)/ALCAPROMPT'
    workflow = re.match(pattern, dataset)
    if not workflow:
        raise ValueError("Couldn't determine workflow out of dataset name {}".format(dataset))
    # TODO #9: check if workflow is correct in autoPCL
    return workflow.group('workflow')


def build_config(dataset, filenames, global_tag, scenario, output_file="alcaConfig.py"):
    # print ("RUN WITH \n{} \n{} \n{} \n{}".format(dataset, filenames, global_tag, scenario))
    from configBuilder import AlCaHarvestingCfgBuilder
    # TODO #13: this thing couples modules
    # from dataDiscovery.discover import extract_workflow
    builder = AlCaHarvestingCfgBuilder()
    input_files = [str(input_file) for input_file in filenames]
    builder.build(str(dataset), extract_workflow(dataset), input_files, scenario, global_tag, output_file)


def prepare_information():

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine('sqlite:///{}'.format(config.runs_db_path), echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    multiruns = session.query(Multirun).filter(Multirun.processed == False, Multirun.closed == True).all()

    #TODO: this should take only one run - which is done now, but with break.
    # It should rather mark it somehow in database that multirun was taken
    for multirun in multiruns:
        multirun_info = dict()
        multirun_info['id'] = multirun.id
        multirun_info['dataset'] = multirun.dataset
        multirun_info['global_tag'] = multirun.global_tag
        multirun_info['scenario'] = multirun.scenario
        multirun_info['cmssw'] = multirun.cmssw
        multirun_info['scram_arch'] = multirun.scram_arch
        filenames = [f.filename for f in multirun.filenames]
        multirun_info['filenames'] = filenames
        dump = json.dumps(multirun_info)
        filename = "params_{}".format(multirun.id)
        with open(filename, "w") as f:
            f.write(dump)

        workspace = "{}/{}".format(config.workspace_path, multirun.scram_arch)
        cmd = "/afs/cern.ch/user/p/poramus/shared/cmsPCLHarvesting/bin/cmssw_env_setup.sh {} {} {} {} {}".format(workspace,
                                                                                                           multirun.cmssw,
                                                                                                           multirun.scram_arch, multirun.id, filename)
        subprocess.call(cmd, shell=True)

        break

def prepare_config(params_file):

    multirun_info = None
    with open(params_file, 'r') as f:
        multirun_info = f.read()

    params = json.loads(multirun_info)

    # TODO: workspace is now defined in two places... not really good
    workspace = "{}/{}".format(config.workspace_path, params['scram_arch'])
    config_file = "{}/{}/src/{}/alcaConfig.py".format(workspace, params['cmssw'], params['id'])

    build_config(params['dataset'], params['filenames'], params['global_tag'], params['scenario'], config_file)