import argparse
import logging
import os
import re
import sqlalchemy
import subprocess
import sys

import model
import logs.logger as logs
import utils.configReader as configReader

""" Tries to upload DQM file to DQM GUI.
    Can be triggered only after the AlCa Harvesting step has finished successfully or the previous DQM upload failed."""


def extract_dataset_parts(dataset):
    pattern = r'/(?P<primary_dataset>.*)/(?P<era_wf_ver>.*?)/ALCAPROMPT'
    ds = re.match(pattern, dataset)
    return ds.group('primary_dataset'), ds.group('era_wf_ver')


if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='pass arbitrary config file', required=False)
    args = parser.parse_args()

    config_file = None
    if args.config:
        config_file = args.config
    config = configReader.read(config_file)

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(config['db_path']), echo=False)
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

        run_numbers = [run.number for run in multirun.run_numbers]
        min_run, max_run = min(run_numbers), max(run_numbers)

        primary_dataset, era_wf_ver = extract_dataset_parts(multirun.dataset.dataset)

        dqm_filename = 'DQM_V0001_R000999999__{}__{}-{}-{}__ALCAPROMPT.root' \
            .format(primary_dataset, era_wf_ver, min_run, max_run)

        eos_dir = multirun.id
        if multirun.retries > 0:
            eos_dir = "{}_{}".format(multirun.id, multirun.retries)

        eos_path = "{}/{}/{}/{}" \
            .format(config['eos_workspace_path'], multirun.scram_arch, multirun.cmssw, eos_dir)

        dqm_file_location = "{}/{}".format(eos_path, dqm_filename)

        script_path = os.path.dirname(os.path.realpath(__file__))
        dqm_script_path = script_path.replace("/python", "/bin/dqm_upload.sh")
        cmd = "{} {} {} {} {} {}".format(dqm_script_path, dqm_filename, dqm_file_location, config['dqm_current'],
                                         config['dqm_upload_host'], multirun.id)
        result = subprocess.call(cmd, shell=True)

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
