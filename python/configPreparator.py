import logging
import sys

from logs.logger import setup_logging
from alcaHarvesting.runner import prepare_config

if __name__ == '__main__':

    setup_logging()
    logger = logging.getLogger(__name__)

    if len(sys.argv) != 2:
        logger.error("Script usage: {} params_file_path".format(sys.argv[0]))
    else:
        params_file_path = sys.argv[1]
        prepare_config(params_file_path)
