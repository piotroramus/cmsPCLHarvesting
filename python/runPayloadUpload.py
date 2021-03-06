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
import t0wmadatasvcApi.t0wmadatasvcApi as t0wmadatasvcApi

""" Tries to upload payload to Dropbox.
    Can be triggered only after the DQM GUI upload has finished successfully or the previous payload upload failed."""


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

    config_file = "config/local.yml"
    if args.config:
        config_file = args.config

    logger.info("Reading config file: {}".format(config_file))
    config = configReader.read(config_file)

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(config['db_path']), echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    # first try to proceed with multi-runs that had not been uploaded before
    multirun = session \
        .query(model.Multirun) \
        .join(model.MultirunState) \
        .filter(model.Multirun.perform_payload_upload == True) \
        .filter(model.MultirunState.state == 'dqm_upload_ok') \
        .first()

    if not multirun:
        multirun = session \
            .query(model.Multirun) \
            .join(model.MultirunState) \
            .filter(model.Multirun.perform_payload_upload == True) \
            .filter(model.MultirunState.state == 'dropbox_upload_failed') \
            .first()

    if not multirun:
        logger.info("Cannot find any multi-runs ready for the payload upload.")
        logger.info("Exiting job.")
    else:
        logger.info("Proceeding with payload upload for multirun {}".format(multirun.id))

        min_run = min(run.number for run in multirun.run_numbers)

        dropbox_failed_state = session \
            .query(model.MultirunState) \
            .filter(model.MultirunState.state == 'dropbox_upload_failed') \
            .one()

        conditions_filename = "promptCalibConditions{}.db".format(multirun.id)
        metadata_filename = "promptCalibConditions{}.txt".format(multirun.id)

        eos_dir = multirun.id
        if multirun.retries > 0:
            eos_dir = "{}_{}".format(multirun.id, multirun.retries)

        eos_path = "{}/{}/{}/{}" \
            .format(config['eos_workspace_path'], multirun.scram_arch, multirun.cmssw, eos_dir)
        script_path = os.path.dirname(os.path.realpath(__file__))
        payload_script_path = script_path.replace("/python", "/bin/payload_upload.sh")
        cmd = "{} {} {} {} {} {} {}".format(payload_script_path, eos_path, conditions_filename, metadata_filename,
                                         multirun.scram_arch, multirun.cmssw, multirun.id)

        result = subprocess.call(cmd, shell=True)

        if result != 0:
            multirun.state = dropbox_failed_state
            session.commit()
            sys.exit(1)

        uploads_ok_state = session \
            .query(model.MultirunState) \
            .filter(model.MultirunState.state == 'uploads_ok') \
            .one()

        multirun.state = uploads_ok_state
        session.commit()
