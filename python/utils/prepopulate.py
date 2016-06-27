import logging

import model
import logs.logger as logs
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def prepopulate(config):
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    engine = create_engine('sqlite:///{}'.format(config['runs_db_path']), echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    # check if there are some states
    sts = session.query(model.MultirunState).all()
    if not sts:
        logger.info("Multirun state table is empty. Populating...")
        states = ['need_more_data', 'ready', 'processing', 'processed_ok', 'no_payload']
        # need_more_data - waiting for more data
        # ready - ready to be processed
        # processing - AlCa harvesting step in progress
        # processed_ok - successfully processed
        # no_payload - needs more data
        # retry - something failed

        for state in states:
            s = model.MultirunState(state=state)
            session.add(s)

        session.commit()
