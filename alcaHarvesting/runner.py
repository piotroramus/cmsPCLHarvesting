import argparse
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from logs.logger import setup_logging
from model import Base, Multirun
from config import runs_db_path

setup_logging()
logger = logging.getLogger(__name__)

# change this to https://github.com/cms-sw/cmssw/blob/CMSSW_8_1_X/Configuration/AlCa/python/autoPCL.py
mapping = {
    'PromptCalibProd': ['BeamSpotByRun', 'BeamSpotByLumi', 'SiStripQuality'],
    'PromptCalibProdSiStrip': ['SiStripQuality'],
    'PromptCalibProdSiStripGains': ['SiStripGains'],
    'PromptCalibProdSiPixelAli': ['SiPixelAli']
}


# TODO: rethink name
def alca_harvest(dataset, filenames, global_tag, scenario):
    print ("RUN WITH \n{} \n{} \n{} \n{}".format(dataset, filenames, global_tag, scenario))
    from configBuilder import AlCaHarvestingCfgBuilder
    from dataDiscovery.discover import extract_workflow
    builder = AlCaHarvestingCfgBuilder()
    input_files = [str(input_file) for input_file in filenames]
    builder.build(str(dataset), extract_workflow(dataset), input_files, scenario, global_tag, "alcaConfig.py")


def parse_multirun_info():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', help='Dataset containing multirun files', required=True)
    parser.add_argument('--filenames', help='List of files to be processed', required=True, metavar='FILENAME',
                        nargs='+')
    parser.add_argument('--global_tag', help='GLOBAL TAG for AlCaHarvesting step', required=True)
    parser.add_argument('--scenario', help='Scenario for AlCaHarvesting step', required=True)
    parser.add_argument('--workflow', help='Workflow for AlCaHarvesting step', required=True)

    return parser.parse_args()


def main():
    engine = create_engine('sqlite:///{}'.format(runs_db_path), echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    m = session.query(Multirun).filter(Multirun.processed == False, Multirun.closed == True).first()
    print "FIRST MULTIRUN: {}".format(m)
    alca_harvest(m.dataset, m.filenames, m.global_tag, m.scenario)
