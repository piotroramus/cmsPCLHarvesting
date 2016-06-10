import logging
import sys

import config
import model
import logs.logger as logs

if __name__ == '__main__':

    logs.setup_logging()
    logger = logging.getLogger(__name__)

    if len(sys.argv) != 2:
        logger.error("Script usage: {} multirun_id".format(sys.argv[0]))
    else:
        multirun_id = sys.argv[1]

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine('sqlite:///{}'.format(config.runs_db_path), echo=False)
        model.Base.metadata.create_all(engine, checkfirst=True)
        Session = sessionmaker(bind=engine)
        session = Session()

        multirun = session.query(model.Multirun).filter(model.Multirun.id == multirun_id).one()

        logger.info("Setting multirun {} processed property to False")

        multirun.processed = False
        session.commit()
