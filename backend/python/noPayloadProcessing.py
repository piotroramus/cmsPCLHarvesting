import argparse
import logging
import sqlalchemy

import model
import logs.logger as logs
import utils.configReader as configReader
import utils.dbConnection as dbConnection

if __name__ == '__main__':

    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("multirun_id", type=int, help="id of processed multi-run")
    parser.add_argument("max_retries", type=int, help="number of times which multi-run can be repeated")
    parser.add_argument("config_file", help="path to configuration file")
    args = parser.parse_args()

    multirun_id = args.multirun_id
    max_retries = args.max_retries
    config_file = args.config_file

    config = configReader.read(config_file)

    connection_string = dbConnection.oracle_connection_string(config)
    engine = sqlalchemy.create_engine(connection_string, echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    multirun = session.query(model.Multirun).filter(model.Multirun.id == multirun_id).one()
    logger.info("Switching multirun {} state to need_more_data".format(multirun_id))
    need_more_data_state = session \
        .query(model.MultirunState) \
        .filter(model.MultirunState.state == 'need_more_data') \
        .one()
    multirun.state = need_more_data_state

    # TODO: might be good to distinguish between 'increasing payload retries' and 'failure retries'
    logger.info("Increasing number of retries")
    multirun.retries = multirun.retries + 1

    session.commit()
