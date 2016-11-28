import logging

import model
import logs.logger as logs


def get_job_types():
    job_types = [
        'discovery',
        'harvesting',
        'dqm_upload',
        'payload_upload'
    ]
    return job_types


def get_states():
    states = [
        'need_more_data',  # waiting for more data
        'ready',  # ready to be processed
        'processing',  # AlCa harvesting step in progress
        'processed_ok',  # successfully processed - ready for DQM upload
        'processing_failed',  # maximum failure retries reached
        'dqm_upload_ok',  # DQM upload was successful - ready for payload upload
        'dqm_upload_failed',  # upload of DQM file failed
        'dropbox_upload_failed',  # payload upload to dropbox failed
        'uploads_ok'  # DQM and payload uploads completed successfully
    ]
    return states


def prepopulate(session):
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    # check states and job types are predefined in the database
    sts = session.query(model.MultirunState).all()
    job_types = session.query(model.JenkinsJobType).all()
    if not sts or not job_types:
        logger.info("Multirun state table is empty. Populating...")
        states = get_states()
        for state in states:
            s = model.MultirunState(state=state)
            session.add(s)

        job_types = get_job_types()
        for job_type in job_types:
            jt = model.JenkinsJobType(type=job_type)
            session.add(jt)

        session.commit()
