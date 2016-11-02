import argparse
import logging

import logs.logger as logs
import alcaHarvesting.envAssembler

if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='pass arbitrary config file', required=False)
    parser.add_argument('--jenkinsJob', help='URL to Jenkins job', required=False)
    args = parser.parse_args()

    config_file = args.config
    jenkins_job = args.jenkinsJob

    logger.info("Preparing AlCa Harvesting config")
    alcaHarvesting.envAssembler.prepare_multirun_environment(config_file)
    logger.info("AlCa Harvesting has been finished")
