import argparse
import logging
import sqlalchemy

import model
import logs.logger as logs

if __name__ == '__main__':

    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("multirun_id", help="id of processed multi-run")
    parser.add_argument("db_path", help="location of database containing multi-run info")
    parser.add_argument("max_retries", help="number of times which multi-run should be repeated in case of failures")
    args = parser.parse_args()

    multirun_id = args.multirun_id
    db_path = args.db_path
    max_retries = args.max_retries

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(db_path), echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    multirun = session.query(model.Multirun).filter(model.Multirun.id == multirun_id).one()
    logger.info("Multirun {} failed. It was retried {}/{} times.".format(multirun.id, multirun.retries, max_retries))
    if multirun.retries == max_retries:
        logger.error("Maximum number of retries reached!")
        # TODO: think what should be done
        pass
    else:
        logger.info("Retrying multi-run - changing the status to ready")
        ready_status = session \
            .query(model.MultirunStatus) \
            .filter(model.MultirunStatus.status == 'ready') \
            .one()
        multirun.status = ready_status
        multirun.retries = multirun.retries + 1

    session.commit()
