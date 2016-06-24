import argparse
import logging

import logs.logger as logs
import alcaHarvesting.envAssembler

if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("params_file", help="path to file containing multi-run parameters")
    args = parser.parse_args()

    params_file_path = args.params_file
    alcaHarvesting.envAssembler.prepare_config(params_file_path)
