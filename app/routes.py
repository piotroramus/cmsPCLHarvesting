import os 
import subprocess

from app import db
from app import app
from flask import g, jsonify, abort, request, make_response, render_template
from sqlalchemy.exc import IntegrityError
from datetime import datetime

import config
import traceback

from os.path import join

from .models import User

# This app relies on authentication being done in the frontend process via SSO.

# --- GET index

@app.route('/')
@app.route('/index')
def index():
    gitInfo = run_in_shell('/usr/bin/git describe --all --long', shell = True)
    return render_template('index.html', lastUpdate=datetime.utcnow(), gitInfo=gitInfo)

@app.route('/heartbeat')
def heartbeat():
    gitInfo = run_in_shell('/usr/bin/git describe --all --long', shell = True)
    return jsonify( {'lastUpdate' : datetime.utcnow(), 'gitInfo' : gitInfo } )

# a simple "echo" method
@app.route('/echo/<string:what>', methods=['POST'])
def echo(what):
    return jsonify( { 'echo' : str(what) } )

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
