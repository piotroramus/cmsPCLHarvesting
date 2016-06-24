import argparse
import logging
import sqlalchemy

import model
import logs.logger as logs

if __name__ == '__main__':

    # TODO: it might be possible to extract similar logic from uprocessedMultirun.py

    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("multirun_id", help="id of processed multi-run")
    parser.add_argument("db_path", help="location of database containing multi-run info")
    args = parser.parse_args()

    multirun_id = args.multirun_id
    db_path = args.db_path

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(db_path), echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    multirun = session.query(model.Multirun).filter(model.Multirun.id == multirun_id).one()
    processed_status = session\
        .query(model.MultirunStatus)\
        .filter(model.MultirunStatus.status == 'processed_ok')\
        .one()
    multirun.status = processed_status
    session.commit()

    logger.info("I will somehow handle the result of the AlCaHarvesting step.")
    logger.info("I should upload DropBox payload.")
    logger.info("If there is no payload, then I should update local DB, thus opening multirun again.")
