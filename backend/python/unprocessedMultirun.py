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
    parser.add_argument("max_failure_retries", type=int,
                        help="number of times which multi-run can be repeated in case of failure")
    parser.add_argument("config_file", help="path to configuration file")
    parser.add_argument('--oracleSecret', help='file containing oracle connection credentials', required=False)
    args = parser.parse_args()

    multirun_id = args.multirun_id
    max_failure_retries = args.max_failure_retries
    config_file = args.config_file
    oracle_secret = args.oracleSecret

    config = configReader.read(config_file)
    config['oracle_secret'] = oracle_secret

    connection_string = dbConnection.get_connection_string(config)
    engine = sqlalchemy.create_engine(connection_string, echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    multirun = session.query(model.Multirun).filter(model.Multirun.id == multirun_id).one()
    logger.info("Multirun {} failed. It was retried {}/{} times.".
                format(multirun.id, multirun.failure_retries, max_failure_retries))
    if multirun.failure_retries >= max_failure_retries:
        logger.error("Maximum number of failure retries reached!")
        logger.info("Changing multi-run status to failed")
        failed_state = session \
            .query(model.MultirunState) \
            .filter(model.MultirunState.state == 'processing_failed') \
            .one()
        multirun.state = failed_state
    else:
        logger.info("Retrying multi-run - changing the state to ready")
        ready_state = session \
            .query(model.MultirunState) \
            .filter(model.MultirunState.state == 'ready') \
            .one()
        multirun.state = ready_state
        multirun.failure_retries = multirun.failure_retries + 1

    session.commit()
