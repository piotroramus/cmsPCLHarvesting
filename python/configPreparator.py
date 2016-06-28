import argparse
import logging

import logs.logger as logs
import alcaHarvesting.envAssembler

if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("params_file", help="path to file containing multi-run parameters")
    parser.add_argument("alca_config", help="name of output config file")
    args = parser.parse_args()

    params_file_path = args.params_file
    alca_config_file = args.alca_config
    alcaHarvesting.envAssembler.prepare_config(params_file_path, alca_config_file)
