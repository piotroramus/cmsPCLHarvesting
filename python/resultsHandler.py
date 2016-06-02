import logging

from logs.logger import setup_logging

if __name__ == '__main__':

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("I will somehow handle the result of the AlCaHarvesting step.")
    logger.info("I should upload DropBox payload.")
    logger.info("If there is no payload, then I should update local DB, thus opening multirun again.")
