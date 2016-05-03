import logging

from logs.logger import setup_logging
from alcaHarvesting.runner import main

if __name__ == '__main__':

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting AlCa Harvesting step")
    main()
    logger.info("AlCa Harvesting has been finished")