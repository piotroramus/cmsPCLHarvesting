import argparse
# import logging
from logs.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', help='Dataset containing multirun files', required=True)
parser.add_argument('--filenames', help='List of files to be processed', required=True, metavar='FILENAME', nargs='+')
parser.add_argument('--global_tag', help='GLOBAL TAG for AlCaHarvesting step', required=True)
parser.add_argument('--scenario', help='Scenario for AlCaHarvesting step', required=True)
parser.add_argument('--workflow', help='Workflow for AlCaHarvesting step', required=True)

args = parser.parse_args()