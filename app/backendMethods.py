import subprocess

from app import db
from app import app

from backend.python import model
from backend.python.utils.workflows import extract_dataset_parts


def create_eos_path(multirun):
    paths = []
    path_template = "{}/{}/{}".format(
        app.config['MULTIRUN_CFG']['eos_workspace_path'],
        multirun['scram_arch'],
        multirun['cmssw']
    )
    for eos_dir in multirun['eos_dirs']:
        path = "{}/{}/".format(path_template, eos_dir)
        paths.append(path)
    return paths


def generate_dqm_url(multirun):
    gui_url = app.config['MULTIRUN_CFG']['dqm_upload_host']
    primary_dataset, processed_dataset = extract_dataset_parts(multirun['dataset'])

    run_numbers = [run['number'] for run in multirun['runs']]
    min_run, max_run = min(run_numbers), max(run_numbers)

    dataset = '/{}/{}-{}-{}/ALCAPROMPT' \
        .format(primary_dataset, processed_dataset, min_run, max_run)

    url = ("{}/start?"
           "runnr=999999;"
           "dataset={};"
           "root=AlCaReco;"
           "workspace=Everything;"
           "sampletype=offline_data;").format(gui_url, dataset)
    return url


def get_multiruns_from_db(offset=0, limit=25):
    multiruns = db.session. \
        query(model.Multirun). \
        order_by(model.Multirun.creation_time.desc()). \
        limit(limit). \
        offset(offset). \
        all()
    m_json = [m.to_json() for m in multiruns]
    state_names = get_state_names()
    for m in m_json:
        m['state'] = state_names[m['state']]
        m['eos_dirs'] = create_eos_path(m)
        m['dqm_url'] = generate_dqm_url(m)
    return m_json


def get_state_names():
    state_names = {
        u'need_more_data': "Need more data",
        u'ready': "Ready",
        u'processing': "Processing",
        u'processed_ok': "Processed OK",
        u'processing_failed': "Processing failed",
        u'dqm_upload_ok': "DQM upload OK",
        u'dqm_upload_failed': "DQM upload failed",
        u'dropbox_upload_failed': "Dropbox upload failed",
        u'uploads_ok': "Uploads OK",
    }
    return state_names


def multiruns_total():
    return db.session.query(model.Multirun).count()


def run_in_shell(*popenargs, **kwargs):
    process = subprocess.Popen(*popenargs, stdout=subprocess.PIPE, **kwargs)
    stdout = process.communicate()[0]
    returnCode = process.returncode
    cmd = kwargs.get('args')
    if cmd is None:
        cmd = popenargs[0]
    if returnCode:
        raise subprocess.CalledProcessError(returnCode, cmd)
    return stdout
