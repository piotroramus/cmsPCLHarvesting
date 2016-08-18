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
    args = parser.parse_args()

    multirun_id = args.multirun_id
    db_path = args.db_path

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(db_path), echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    multirun = session.query(model.Multirun).filter(model.Multirun.id == multirun_id).one()
    logger.info("Switching multirun {} state to need_more_data")
    need_more_data_state = session \
        .query(model.MultirunState) \
        .filter(model.MultirunState.state == 'need_more_data') \
        .one()
    multirun.state = need_more_data_state

    # TODO: make it consistent with max_retries
    logger.info("Increasing number of retries")
    multirun.retries = multirun.retries + 1

    session.commit()
