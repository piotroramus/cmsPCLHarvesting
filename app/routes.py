import os
import subprocess

from app import db
from app import app
from flask import g, jsonify, abort, request, make_response, render_template, redirect, url_for
from sqlalchemy.exc import IntegrityError
from datetime import datetime

import config
import traceback

from os.path import join

from .models import User

from backend.python import model
from backend.python.utils.workflows import extract_workflow

from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()


# This app relies on authentication being done in the frontend process via SSO.

# --- GET index

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('display'))


@app.route('/heartbeat')
def heartbeat():
    gitInfo = run_in_shell('/usr/local/bin/git describe --all --long', shell=True)
    return jsonify({'lastUpdate': datetime.utcnow(), 'gitInfo': gitInfo})


# a simple "echo" method
@app.route('/echo/<string:what>', methods=['POST'])
def echo(what):
    return jsonify({'echo': str(what)})


# --- error handlers

@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'message': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return error404()


@app.errorhandler(409)
def integration_error(error):
    return make_response(jsonify({'message': 'Duplicate entry'}), 409)


@app.errorhandler(500)
def internal_error(error):
    return make_response(jsonify({'message': 'Internal server error'}), 500)


# --- utilities

def success():
    return make_response(jsonify({'success': True}), 200)


def error404():
    return make_response(jsonify({'message': 'Not found'}), 404)


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


def get_data(offset=0, limit=25):
    multiruns = db.session. \
        query(model.Multirun). \
        order_by(model.Multirun.creation_time.desc()). \
        limit(limit). \
        offset(offset). \
        all()
    m_json = [m.to_json() for m in multiruns]
    for m in m_json:
        m['state'] = state_names[m['state']]
        m['eos_dirs'] = create_eos_path(m)
    return m_json


def create_eos_path(multirun):
    paths = []
    for d in multirun['eos_dirs']:
        # TODO: can be optimized a little bit
        path = app.config['MULTIRUN_CFG']['eos_workspace_path']
        path = "{}/{}/{}/{}/".format(path, multirun['scram_arch'], multirun['cmssw'], d)
        paths.append(path)
    return paths


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


@app.route('/test/')
def test():
    print get_data()
    return "response"


@app.route('/display_plain/')
def display_plain():
    multiruns = get_data()
    return render_template('plain_table.html', multiruns=multiruns)


@app.route('/m/')
def multirun_new():
    return app.send_static_file('templates/main.html')


@app.route('/display/')
def display():
    return app.send_static_file('templates/index.html')


@app.route('/multiruns/')
def get_multiruns():
    # TODO: common logic with workflow method
    # probably it is worth to only extract getting multiruns to different method
    offset = request.args.get('offset')
    if not offset:
        offset = 0
    limit = request.args.get('limit')
    # TODO: think what to put as a default and also how to get every record
    if not limit:
        limit = 25
    data = get_data(offset, limit)
    return jsonify(multiruns=data,
                   limit=limit,
                   offset=offset,
                   total=multiruns_total())


@app.route('/multiruns_by_workflow/')
def get_multiruns_by_workflow():
    offset = request.args.get('offset')
    if not offset:
        offset = 0
    limit = request.args.get('limit')
    if not limit:
        limit = 0
    data = get_data(offset, limit)
    m_by_workflows = dict()
    for multirun in data:
        workflow = extract_workflow(multirun['dataset'])
        if workflow not in m_by_workflows:
            m_by_workflows[workflow] = [multirun]
        else:
            m_by_workflows[workflow].append(multirun)

    return jsonify(multiruns=m_by_workflows,
                   limit=limit,
                   offset=offset,
                   total=multiruns_total())


@app.route('/multiruns_total/')
def mtotal():
    return jsonify(total=multiruns_total())


def multiruns_total():
    return db.session.query(model.Multirun).count()


@app.route('/color_test/')
def color_test():
    return app.send_static_file('templates/color_test.html')


@app.route('/configuration/')
def get_config():
    # TODO: fix
    # return app.config['MULTIRUN_CFG']['eos_workspace_path']
    return jsonify(config=app.config)
