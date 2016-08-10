import logging

import model
import logs.logger as logs
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def prepopulate(config):
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    engine = create_engine('sqlite:///{}'.format(config['db_path']), echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    # check if there are some states
    sts = session.query(model.MultirunState).all()
    if not sts:
        logger.info("Multirun state table is empty. Populating...")
        states = [
            'need_more_data',  # waiting for more data
            'ready',  # ready to be processed
            'processing',  # AlCa harvesting step in progress
            'processed_ok',  # successfully processed - ready for DQM upload
            'failed',  # maximum retries reached
            'dqm_upload_ok',  # DQM upload was successful - ready for payload upload
            'dqm_upload_failed',  # upload of DQM file failed
            'dropbox_upload_failed',  # payload upload to dropbox failed
            'uploads_ok'  # DQM and payload uploads completed successfully
        ]

        for state in states:
            s = model.MultirunState(state=state)
            session.add(s)

        session.commit()
