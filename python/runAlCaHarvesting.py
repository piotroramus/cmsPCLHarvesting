import logging

import logs.logger as logs
import alcaHarvesting.envAssembler

if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Preparing AlCa Harvesting config")

    alcaHarvesting.envAssembler.prepare_multirun_environment()

    logger.info("AlCa Harvesting has been finished")
