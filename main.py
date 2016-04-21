import logging

from dataDiscovery.harvest import harvest
from logs.logger import setup_logging


if __name__ == '__main__':

    setup_logging()
    logger = logging.getLogger(__name__)

    # TODO #3: consider calling setup.sh here
    logger.info("Starting data discovery")
    harvest()
    logger.info("Data discovery has been finished")
