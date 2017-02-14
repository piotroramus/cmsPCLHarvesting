from __future__ import print_function

import copy
import sys

from datetime import datetime
from flask import g, jsonify, abort, request, make_response, render_template, redirect, url_for
from flask_httpauth import HTTPBasicAuth

from app import app
from backendMethods import get_multiruns_from_db, multiruns_total, run_in_shell
from backend.python.utils.other import extract_workflow

auth = HTTPBasicAuth()


# This app relies on authentication being done in the frontend process via SSO.

# --- GET index

@app.route('/cmsDbMultiRunHarvesting/')
@app.route('/cmsDbMultiRunHarvesting/index')
def index():
    return redirect(url_for('display'))


# --- diagnostics
@app.route('/cmsDbMultiRunHarvesting/heartbeat')
def heartbeat():
    gitInfo = run_in_shell('/usr/local/bin/git describe --all --long', shell=True)
    return jsonify({'lastUpdate': datetime.utcnow(), 'gitInfo': gitInfo})


# a simple "echo" method
@app.route('/cmsDbMultiRunHarvesting/echo/<string:what>', methods=['POST'])
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


# --- Multirun Harvesting concerned methods
@app.route('/cmsDbMultiRunHarvesting/test/')
def test():
    print(get_multiruns_from_db(), file=sys.stderr)
    return "Have a look into logs..."


@app.route('/cmsDbMultiRunHarvesting/plain_display/')
def display_plain():
    multiruns = get_multiruns_from_db()
    return render_template('plain_table.html', multiruns=multiruns)


@app.route('/cmsDbMultiRunHarvesting/basic_template/')
def multirun_new():
    return app.send_static_file('templates/basic.html')


@app.route('/cmsDbMultiRunHarvesting/display/')
def display():
    return app.send_static_file('templates/index.html')


@app.route('/cmsDbMultiRunHarvesting/multiruns/')
def get_multiruns():
    offset = int(request.args.get('offset', default=0))
    limit = int(request.args.get('limit', default=25))
    data = get_multiruns_from_db(offset, limit)
    return jsonify(multiruns=data,
                   limit=limit,
                   offset=offset,
                   total=multiruns_total())


@app.route('/cmsDbMultiRunHarvesting/multiruns_by_workflow/')
def get_multiruns_by_workflow():
    offset = int(request.args.get('offset', default=0))
    limit = int(request.args.get('limit', default=25))
    data = get_multiruns_from_db(offset, limit)
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


@app.route('/cmsDbMultiRunHarvesting/multiruns_total/')
def mtotal():
    return jsonify(total=multiruns_total())


@app.route('/cmsDbMultiRunHarvesting/color_test/')
def color_test():
    return app.send_static_file('templates/color_test.html')


@app.route('/cmsDbMultiRunHarvesting/configuration/')
def get_config():
    # This method can expose a sensitive data, so it in this shape
    # should be only used for debugging!
    config = copy.deepcopy(app.config)
    # date is not json-serializable, so it have to be handled manually
    config['PERMANENT_SESSION_LIFETIME'] = str(config['PERMANENT_SESSION_LIFETIME'])
    return jsonify(config=config)
