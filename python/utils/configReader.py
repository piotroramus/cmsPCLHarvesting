import yaml
import logging

import logs.logger as logs


def read(config_file):
    logger = logging.getLogger(__name__)
    logs.setup_logging()

    result = {}
    with open(config_file, 'r') as stream:
        try:
            result = yaml.load(stream)
        except yaml.YAMLError as exc:
            logger.error("Error while parsing YAML config file {}: {}".format(config_file, exc))

    return result
