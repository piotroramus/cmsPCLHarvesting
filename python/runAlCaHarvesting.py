import logging

from logs.logger import setup_logging
from alcaHarvesting.envAssembler import prepare_multirun_environment

if __name__ == '__main__':

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Preparing AlCa Harvesting config")

    prepare_multirun_environment()

    logger.info("AlCa Harvesting has been finished")