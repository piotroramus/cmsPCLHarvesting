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

    # check if there are some statuses
    sts = session.query(model.MultirunStatus).all()
    if not sts:
        logger.info("Multirun status table is empty. Populating...")
        statuses = ['need_more_data', 'ready', 'processing', 'processed_ok', 'no_payload']
        # need_more_data - waiting for more data
        # ready - ready to be processed
        # processing - AlCa harvesting step in progress
        # processed_ok - successfully processed
        # no_payload - needs more data
        # retry - something failed

        for status in statuses:
            s = model.MultirunStatus(status=status)
            session.add(s)

        session.commit()
