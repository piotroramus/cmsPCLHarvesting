import yaml
import logging
import os

# because _this_ module is imported from different levels
try:
    import logs.logger as logs
except ImportError:
    import backend.python.logs.logger as logs


def read(config_file=None):
    logger = logging.getLogger(__name__)
    logs.setup_logging()

    if not config_file:
        config_file = get_default_config_filename()

    result = {}
    logger.info("Reading config file: {}".format(config_file))
    with open(config_file, 'r') as stream:
        try:
            result = yaml.load(stream)
        except yaml.YAMLError as exc:
            logger.error("Error while parsing YAML config file {}: {}".format(config_file, exc))

    return result


def get_default_config_filename():
    # directory containing THIS script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, "../../../resources/referenceBackendCfgs/local.yml")
