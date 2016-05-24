import logging

from logs.logger import setup_logging
from alcaHarvesting.runner import prepare_information

if __name__ == '__main__':

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Preparing AlCa Harvesting config")

    prepare_information()

    logger.info("AlCa Harvesting has been finished")