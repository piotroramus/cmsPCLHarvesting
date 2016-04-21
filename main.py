import logging

from dataDiscovery.discover import discover
from logs.logger import setup_logging


if __name__ == '__main__':

    setup_logging()
    logger = logging.getLogger(__name__)

    # TODO #3: consider calling setup.sh here
    logger.info("Starting data discovery")
    discover()
    logger.info("Data discovery has been finished")
