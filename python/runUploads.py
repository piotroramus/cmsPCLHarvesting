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

    # TODO: other cases: dqmfailed and dropboxfailed
    multirun = session \
        .query(model.Multirun) \
        .filter(model.MultirunState.state == 'processed_ok') \
        .first()

    if multirun:
        logger.info("Proceeding with DQM file upload for multirun {}".format(multirun.id))
        logger.info("Determining DQM filename...")

        run_numbers = [run.number for run in multirun.run_numbers]
        min_run, max_run = min(run_numbers), max(run_numbers)

        primary_dataset, era_wf_ver = extract_dataset_parts(multirun.dataset.dataset)

        dqm_filename = 'DQM_V0001_R000999999__{}__{}-{}-{}__ALCAPROMPT.root' \
            .format(primary_dataset, era_wf_ver, min_run, max_run)

        eos_path = "{}/{}/{}/{}" \
            .format(config['eos_workspace_path'], multirun.scram_arch, multirun.cmssw, multirun.eos_dir)

        dqm_file_location = "{}/{}".format(eos_path, dqm_filename)

        script_path = os.path.dirname(os.path.realpath(__file__))
        dqm_script_path = script_path.replace("/python", "/bin/dqm_upload.sh")
        cmd = "{} {} {} {} {}".format(dqm_script_path, dqm_filename, dqm_file_location, config['dqm_current'],
                                      config['dqm_upload_host'])
        result = subprocess.call(cmd, shell=True)

        if result != 0:
            dqm_failed_state = session \
                .query(model.MultirunState) \
                .filter(model.MultirunState.state == 'dqm_upload_failed') \
                .one()
            multirun.state = dqm_failed_state
            session.commit()
            sys.exit(1)

        conditions_filename = "promptCalibConditions{}.db".format(multirun.id)
        metadata_filename = "promptCalibConditions{}.txt".format(multirun.id)

        payload_script_path = script_path.replace("/python", "/bin/payload_upload.sh")
        cmd = "{} {} {} {} {} {}".format(payload_script_path, eos_path, conditions_filename, metadata_filename,
                                         multirun.scram_arch, multirun.cmssw)

        result = subprocess.call(cmd, shell=True)

        if result != 0:
            dropbox_failed_state = session \
                .query(model.MultirunState) \
                .filter(model.MultirunState.state == 'dropbox_upload_failed') \
                .one()
            multirun.state = dropbox_failed_state
            session.commit()
            sys.exit(1)

        uploads_ok_state = session \
            .query(model.MultirunState) \
            .filter(model.MultirunState.state == 'uploads_ok') \
            .one()

        multirun.state = uploads_ok_state
        session.commit()
