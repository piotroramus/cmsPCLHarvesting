import argparse
import logging
import sqlalchemy

import model
import logs.logger as logs

if __name__ == '__main__':

    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("multirun_id", type=int, help="id of processed multi-run")
    parser.add_argument("db_path", help="location of database containing multi-run info")
    parser.add_argument("max_retries", type=int, help="number of times which multi-run can be repeated")
    args = parser.parse_args()

    multirun_id = args.multirun_id
    db_path = args.db_path
    max_retries = args.max_retries

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(db_path), echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    session.commit()

    multirun = session.query(model.Multirun).filter(model.Multirun.id == multirun_id).one()
    if multirun.retries >= max_retries:
        logger.error("Maximum number of retries reached!")
        logger.info("Changing multi-run status to failed")
        failed_state = session \
            .query(model.MultirunState) \
            .filter(model.MultirunState.state == 'processing_failed') \
            .one()
        multirun.state = failed_state
    else:
        logger.info("Switching multirun {} state to need_more_data".format(multirun_id))
        need_more_data_state = session \
            .query(model.MultirunState) \
            .filter(model.MultirunState.state == 'need_more_data') \
            .one()
        multirun.state = need_more_data_state

        logger.info("Increasing number of retries")
        multirun.retries = multirun.retries + 1

    session.commit()
