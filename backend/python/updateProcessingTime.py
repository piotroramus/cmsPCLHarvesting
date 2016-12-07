import argparse
import datetime
import logging
import sqlalchemy

import model
import logs.logger as logs
import utils.configReader as configReader
import utils.dbConnection as dbConnection

if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    now = datetime.datetime.now()

    parser = argparse.ArgumentParser()
    parser.add_argument("multirun_id", type=int, help="id of the processed multi-run")
    parser.add_argument("config_file", help="path to configuration file containing DB connection information")
    parser.add_argument("processing_sort", choices=['start', 'end'],
                        help="whether to update start or end processing time")
    parser.add_argument('--oracleSecret', help='file containing oracle connection credentials', required=False)

    args = parser.parse_args()

    multirun_id = args.multirun_id
    config_file = args.config_file
    processing_sort = args.processing_sort
    oracle_secret = args.oracleSecret

    config = configReader.read(config_file)
    config['oracle_secret'] = oracle_secret

    connection_string = dbConnection.get_connection_string(config)
    engine = sqlalchemy.create_engine(connection_string, echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    if processing_sort == 'start':
        logger.info("Updating multi-run processing start time with {}".format(now))
        processing_time_obj = model.ProcessingTime()
        processing_time_obj.start_time = now
        processing_time_obj.multirun_id = multirun_id
        session.add(processing_time_obj)
    else:
        # at the same time only one multi-run can be processed so we can be sure
        # that there should be exactly one multi-run that has a start_time and does not have an end_time
        # (assuming this script is invoked after the processing is finished)
        logger.info("Updating multi-run processing end time with {}".format(now))
        processing_time_obj = session \
            .query(model.ProcessingTime) \
            .filter(model.ProcessingTime.multirun_id == multirun_id) \
            .filter(model.ProcessingTime.start_time != None) \
            .filter(model.ProcessingTime.end_time == None) \
            .one()
        processing_time_obj.end_time = now

    session.commit()
