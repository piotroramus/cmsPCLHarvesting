import logging
import json
import subprocess
import os

import config
import utils.workflows as workflows
import logs.logger as logs

from model import Base, Multirun

logs.setup_logging()
logger = logging.getLogger(__name__)


def build_config(dataset, filenames, global_tag, scenario, output_file="alcaConfig.py"):
    from configBuilder import AlCaHarvestingCfgBuilder
    builder = AlCaHarvestingCfgBuilder()
    input_files = [str(input_file) for input_file in filenames]
    builder.build(str(dataset), workflows.extract_workflow(dataset), input_files, scenario, global_tag, output_file)


def prepare_multirun_environment():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine('sqlite:///{}'.format(config.runs_db_path), echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    multirun = session.query(Multirun).filter(Multirun.processed == False, Multirun.closed == True).first()

    if not multirun:
        logger.info("No closed and unprocessed multiruns found - no further steps will be taken")

    else:
        logger.info("Multirun to be processed: {}".format(multirun))

        multirun.processed = True
        session.commit()

        multirun_info = dict()
        multirun_info['id'] = multirun.id
        multirun_info['dataset'] = multirun.dataset
        multirun_info['global_tag'] = multirun.global_tag
        multirun_info['scenario'] = multirun.scenario
        multirun_info['cmssw'] = multirun.cmssw
        multirun_info['scram_arch'] = multirun.scram_arch
        filenames = [f.filename for f in multirun.filenames]
        multirun_info['filenames'] = filenames
        dump = json.dumps(multirun_info)
        filename = "params_{}".format(multirun.id)
        with open(filename, "w") as f:
            f.write(dump)

        workspace = "{}/{}".format(config.workspace_path, multirun.scram_arch)
        script_path = os.path.dirname(os.path.realpath(__file__))
        shell_script_path = script_path.replace("/python/alcaHarvesting", "/bin/cmssw_env_setup.sh")
        python_dir_path = script_path.replace("/alcaHarvesting", "/")
        cmd = "{} {} {} {} {} {} {} {} {}".format(shell_script_path, workspace, multirun.cmssw, multirun.scram_arch,
                                                  multirun.id, filename, python_dir_path, config.dqm_current,
                                                  config.dqm_upload_host)
        subprocess.call(cmd, shell=True)


def prepare_config(params_file):
    multirun_info = None
    with open(params_file, 'r') as f:
        multirun_info = f.read()

    params = json.loads(multirun_info)

    config_file = "alcaConfig.py"
    build_config(params['dataset'], params['filenames'], params['global_tag'], params['scenario'], config_file)
