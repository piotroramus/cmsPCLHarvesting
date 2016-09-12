import logging
import json
import subprocess
import os

import utils.workflows as workflows
import logs.logger as logs
import utils.configReader as configReader
import utils.dbConnection as dbConnection

from model import Base, Multirun, MultirunState

logs.setup_logging()
logger = logging.getLogger(__name__)


def dataset_with_runs_range(dataset, runs_range):
    import re
    pattern = r'(?P<slice>.*)/ALCAPROMPT'
    substitution = r'\g<slice>-{}/ALCAPROMPT'.format(runs_range)
    result = re.sub(pattern, substitution, dataset)
    return result


def prepare_config(params_file, alca_config_file="alcaConfig.py", job_report_file="FrameworkJobReport.xml"):
    from configBuilder import AlCaHarvestingCfgBuilder
    multirun_info = None
    with open(params_file, 'r') as f:
        multirun_info = f.read()

    params = json.loads(multirun_info)

    dataset = str(params['dataset'])
    global_tag = params['global_tag']
    scenario = params['scenario']
    input_files = [str(input_file) for input_file in params['filenames']]
    runs = params['runs']
    min_run, max_run = min(runs), max(runs)
    runs_range = "{}-{}".format(min_run, max_run)

    builder = AlCaHarvestingCfgBuilder()
    dataset_with_rr = dataset_with_runs_range(str(dataset), runs_range)
    builder.build(dataset_with_rr, workflows.extract_workflow(dataset), input_files, scenario, global_tag,
                  alca_config_file, job_report_file)


def prepare_multirun_environment(config_file):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    config = configReader.read(config_file)

    connection_string = dbConnection.get_connection_string(config)
    engine = create_engine(connection_string, echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    logger.info("Searching for a ready to be processed multi-run...")
    ready_state = session.query(MultirunState).filter(MultirunState.state == 'ready').one()
    multirun = session.query(Multirun).filter(Multirun.state == ready_state).first()

    if not multirun:
        logger.info("Cannot find any multi-run ready to be processed - no further steps will be taken")

    else:
        logger.info("Multirun to be processed: {}".format(multirun))

        processing_state = session.query(MultirunState).filter(MultirunState.state == 'processing').one()
        multirun.state = processing_state

        filenames = [f.filename for f in multirun.filenames]
        runs = [run.number for run in multirun.run_numbers]

        multirun_info = dict()
        multirun_info['id'] = multirun.id
        multirun_info['dataset'] = multirun.dataset.dataset
        multirun_info['global_tag'] = multirun.global_tag
        multirun_info['scenario'] = multirun.scenario
        multirun_info['cmssw'] = multirun.cmssw
        multirun_info['scram_arch'] = multirun.scram_arch
        multirun_info['filenames'] = filenames
        multirun_info['runs'] = runs
        dump = json.dumps(multirun_info)

        multirun_props_file = "multirunProperties{}.txt".format(multirun.id)
        logger.info("Creating {} file containing multi-run information".format(multirun_props_file))
        with open(multirun_props_file, 'w') as f:
            f.write(dump)

        script_path = os.path.dirname(os.path.realpath(__file__))
        python_dir_path = script_path.replace("/alcaHarvesting", "")
        absolute_python_dir_path = os.path.abspath(python_dir_path)
        db_path = os.path.abspath(config['db_path'])

        multirun_dir = multirun.id
        if multirun.failure_retries > 0 or multirun.no_payload_retries:
            multirun_dir = "{}_{}p_{}f".format(multirun.id, multirun.no_payload_retries, multirun.failure_retries)

        shell_props_file = "shellProperties{}.txt".format(multirun.id)
        logger.info("Creating {} file containing parameters used by various scripts".format(shell_props_file))
        with open(shell_props_file, 'w') as f:
            f.write("EOS_WORKSPACE={}\n".format(config['eos_workspace_path']))
            f.write("CMSSW_RELEASE={}\n".format(multirun.cmssw))
            f.write("SCRAM_ARCH={}\n".format(multirun.scram_arch))
            f.write("MULTIRUN_ID={}\n".format(multirun.id))
            f.write("MULTIRUN_DIR={}\n".format(multirun_dir))
            f.write("ALCA_CONFIG_FILE={}\n".format(config['alca_config']))
            f.write("JOB_REPORT_FILE={}\n".format(config['job_report']))
            f.write("CMS_RUN_OUTPUT={}\n".format(config['cms_run_output']))
            f.write("MULTIRUN_PROPS_FILE={}\n".format(multirun_props_file))
            f.write("PYTHON_DIR_PATH={}\n".format(absolute_python_dir_path))
            f.write("DQM_UPLOAD_HOST={}\n".format(config['dqm_upload_host']))
            f.write("MAX_FAILURE_RETRIES={}\n".format(config['max_failure_retries']))
            f.write("FAILURE_RETRIES={}\n".format(multirun.failure_retries))
            f.write("NO_PAYLOAD_RETRIES={}\n".format(multirun.no_payload_retries))
            f.write("CONFIG_FILE={}\n".format(config_file))

        # commit is down here to assure that state will be changed to 'processing' after serialisation goes well
        session.commit()

        shell_script_path = script_path.replace("/python/alcaHarvesting", "/bin/cmssw_env_setup.sh")
        cmd = "{} {}".format(shell_script_path, shell_props_file)
        logger.info("Invoking script:\n\t {}".format(cmd))
        subprocess.call(cmd, shell=True)
