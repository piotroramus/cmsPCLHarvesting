import logging
import json
import subprocess

import config
import utils.workflows as workflows

from logs.logger import setup_logging
from model import Base, Multirun

setup_logging()
logger = logging.getLogger(__name__)


def build_config(dataset, filenames, global_tag, scenario, output_file="alcaConfig.py"):
    from configBuilder import AlCaHarvestingCfgBuilder
    builder = AlCaHarvestingCfgBuilder()
    input_files = [str(input_file) for input_file in filenames]
    builder.build(str(dataset), workflows.extract_workflow(dataset), input_files, scenario, global_tag, output_file)


def prepare_information():

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine('sqlite:///{}'.format(config.runs_db_path), echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    multiruns = session.query(Multirun).filter(Multirun.processed == False, Multirun.closed == True).all()

    #TODO: this should take only one run - which is done now, but with break.
    # It should rather mark it somehow in database that multirun was taken
    for multirun in multiruns:
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
        cmd = "/afs/cern.ch/user/p/poramus/shared/cmsPCLHarvesting/bin/cmssw_env_setup.sh {} {} {} {} {}".format(workspace,
                                                                                                           multirun.cmssw,
                                                                                                           multirun.scram_arch, multirun.id, filename)
        subprocess.call(cmd, shell=True)

        break

def prepare_config(params_file):

    multirun_info = None
    with open(params_file, 'r') as f:
        multirun_info = f.read()

    params = json.loads(multirun_info)

    # TODO: workspace is now defined in two places... not really good
    workspace = "{}/{}".format(config.workspace_path, params['scram_arch'])
    config_file = "{}/{}/src/{}/alcaConfig.py".format(workspace, params['cmssw'], params['id'])

    build_config(params['dataset'], params['filenames'], params['global_tag'], params['scenario'], config_file)