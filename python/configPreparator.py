import logging
import sys

from logs.logger import setup_logging
from alcaHarvesting.runner import prepare_config

if __name__ == '__main__':

    setup_logging()
    logger = logging.getLogger(__name__)

    if len(sys.argv) != 2:
        logger.error("Script usage: {} parameters_file".format(sys.argv[0]))
    else:
        prepare_config(sys.argv[1])
