import argparse
import logging
import sqlalchemy

import model
import logs.logger as logs
import dataDiscovery.discover
import utils.configReader as configReader
import utils.prepopulate as prepopulate


if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='pass arbitrary config file', required=False)
    args = parser.parse_args()

    config_file = "config/local.yml"
    if args.config:
        config_file = args.config

    logger.info("Reading config file: {}".format(config_file))
    config = configReader.read(config_file)

    logger.info("Prepopulating database if needed")
    prepopulate.prepopulate(config)

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(config['db_path']), echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    logger.info("Starting data discovery")
    dataDiscovery.discover.discover(config, session)
    dataDiscovery.discover.assembly_multiruns(config, session)
    logger.info("Data discovery has been finished")
