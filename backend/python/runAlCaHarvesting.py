import argparse
import logging

import logs.logger as logs
import alcaHarvesting.envAssembler
import utils.configReader as configReader

if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='pass arbitrary config file', required=False)
    args = parser.parse_args()

    config_file = "config/local.yml"
    if args.config:
        config_file = args.config

    logger.info("Reading config file: {}".format(config_file))
    config = configReader.read(config_file)

    logger.info("Preparing AlCa Harvesting config")
    alcaHarvesting.envAssembler.prepare_multirun_environment(config)
    logger.info("AlCa Harvesting has been finished")
