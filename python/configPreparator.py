import logging
import sys

import logs.logger as logs
import alcaHarvesting.envAssembler

if __name__ == '__main__':

    logs.setup_logging()
    logger = logging.getLogger(__name__)

    if len(sys.argv) != 2:
        logger.error("Script usage: {} params_file_path".format(sys.argv[0]))
    else:
        params_file_path = sys.argv[1]
        alcaHarvesting.envAssembler.prepare_config(params_file_path)
