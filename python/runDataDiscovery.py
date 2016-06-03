import logging

import logs.logger as logs
import dataDiscovery.discover

if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting data discovery")
    dataDiscovery.discover.discover()
    logger.info("Data discovery has been finished")
