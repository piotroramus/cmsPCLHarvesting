import argparse
import logging
import sqlalchemy

import model
import logs.logger as logs
import utils.configReader as configReader

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

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(config['db_path']), echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    multiruns_processed_ok = session \
        .query(model.Multirun) \
        .filter(model.MultirunState == 'processed_ok') \
        .all()

    for multirun in multiruns_processed_ok:
        logger.info("Proceeding with uploads for multirun {}".format(multirun.id))
