import logging
import sys

import model
import logs.logger as logs
import utils.prepopulate


def update_jenkins_build_url(multirun_id, url, job_type, config, session):
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    job_types = utils.prepopulate.get_job_types()
    if job_type not in job_types:
        logger.error("Jenkins Job Type {} not forseen!".format(job_type))
        sys.exit(1)

    type_obj = session \
        .query(model.JenkinsJobType) \
        .filter(model.JenkinsJobType.type == job_type) \
        .one()

    logger.info("Adding Jenkins Build Url {} for multirun {}".format(url, multirun_id))
    jenkins_url_obj = model.JenkinsBuildUrl()
    jenkins_url_obj.url = url
    jenkins_url_obj.multirun_id = multirun_id
    jenkins_url_obj.type = type_obj
    session.add(jenkins_url_obj)

    session.commit()
