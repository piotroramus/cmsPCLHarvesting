import argparse
import logging
import os
import sqlalchemy
import subprocess
import sys

import model
import logs.logger as logs
import utils.configReader as configReader
import utils.dbConnection as dbConnection
import utils.jenkins as jenkins
import utils.other as utils

""" Tries to upload DQM file to DQM GUI.
    Can be triggered only after the AlCa Harvesting step has finished successfully or the previous DQM upload failed."""

if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='pass arbitrary config file', required=False)
    parser.add_argument('--jenkinsBuildUrl', help='URL to Jenkins job', required=False)
    parser.add_argument('--oracleSecret', help='file containing oracle connection credentials', required=False)
    args = parser.parse_args()

    jenkins_build_url = args.jenkinsBuildUrl
    oracle_secret = args.oracleSecret

    config_file = args.config
    config = configReader.read(config_file)
    config['oracle_secret'] = oracle_secret

    connection_string = dbConnection.get_connection_string(config)
    engine = sqlalchemy.create_engine(connection_string, echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    # first try to proceed with multi-runs that had not been uploaded before
    multirun = session \
        .query(model.Multirun) \
        .join(model.MultirunState) \
        .filter(model.MultirunState.state == 'processed_ok') \
        .first()

    if not multirun:
        multirun = session \
            .query(model.Multirun) \
            .join(model.MultirunState) \
            .filter(model.MultirunState.state == 'dqm_upload_failed') \
            .first()

    if not multirun:
        logger.info("Cannot find any processed multi-runs ready for the DQM upload.")
        logger.info("Exiting job.")
    else:
        logger.info("Proceeding with DQM file upload for multirun {}".format(multirun.id))
        logger.info("Determining DQM filename...")

        run_numbers = [run.number for run in multirun.runs]
        min_run, max_run = min(run_numbers), max(run_numbers)

        primary_dataset, processed_dataset = utils.extract_dataset_parts(multirun.dataset.dataset)

        dqm_filename = 'DQM_V0001_R000999999__{}__{}-{}-{}__ALCAPROMPT.root' \
            .format(primary_dataset, processed_dataset, min_run, max_run)

        multirun_dir = multirun.id
        if multirun.failure_retries > 0 or multirun.no_payload_retries:
            multirun_dir = "{}_{}p_{}f".format(multirun.id, multirun.no_payload_retries, multirun.failure_retries)

        eos_path = "{}/{}/{}/{}" \
            .format(config['eos_workspace_path'], multirun.scram_arch, multirun.cmssw, multirun_dir)

        dqm_file_location = "{}/{}".format(eos_path, dqm_filename)

        script_path = os.path.dirname(os.path.realpath(__file__))
        dqm_script_path = script_path.replace("/python", "/bin/dqm_upload.sh")
        cmd = "{} {} {} {} {} {}".format(dqm_script_path, dqm_filename, dqm_file_location, config['dqm_upload_host'],
                                         multirun.id, script_path)
        result = subprocess.call(cmd, shell=True)

        jenkins.update_jenkins_build_url(multirun.id, jenkins_build_url, job_type="dqm_upload",
                                         config=config, session=session)

        if result != 0:
            dqm_failed_state = session \
                .query(model.MultirunState) \
                .filter(model.MultirunState.state == 'dqm_upload_failed') \
                .one()
            multirun.state = dqm_failed_state
            session.commit()
            sys.exit(1)

        dqm_upload_ok = session \
            .query(model.MultirunState) \
            .filter(model.MultirunState.state == 'dqm_upload_ok') \
            .one()

        multirun.state = dqm_upload_ok
        session.commit()
