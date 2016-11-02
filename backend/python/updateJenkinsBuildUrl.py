import argparse
import logging
import sys
import sqlalchemy

import model
import logs.logger as logs
import utils.configReader as configReader
import utils.dbConnection as dbConnection
import utils.prepopulate


def update_jenkins_build_url(multirun_id, url, type, config, logger):
    if type not in utils.prepopulate.job_types:
        logger.error("Jenkins Job Type {} not forseen!".format(type))
        sys.exit(1)

    connection_string = dbConnection.get_connection_string(config)
    engine = sqlalchemy.create_engine(connection_string, echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    type_obj = session \
        .query(model.JenkinsJobType) \
        .filter(model.JenkinsJobType.type == type) \
        .one()

    logger.info("Adding Jenkins Build Url {} for multirun {}".format(url, multirun_id))
    jenkins_url_obj = model.JenkinsBuildUrl()
    jenkins_url_obj.url = url
    jenkins_url_obj.multirun_id = multirun_id
    jenkins_url_obj.type = type_obj
    session.add(jenkins_url_obj)

    session.commit()


if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("multirun_id", type=int, help="id of processed multi-run")
    parser.add_argument("jenkins_url", help="URL to Jenkins job")
    parser.add_argument("config_file", help="path to configuration file")
    args = parser.parse_args()

    multirun_id = args.multirun_id
    jenkins_url = args.jenkins_url
    config_file = args.config_file

    config = configReader.read(config_file)

    update_jenkins_build_url(multirun_id, jenkins_url, type="harvesting", config=config, logger=logger)
