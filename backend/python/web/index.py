import os
import buprocess
import sys


import python.model as model
import utils.configReader as configReader

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

from web.app import db
from web.app import app
from flask import g, jsonify, abort, request, make_response, render_template
from sqlalchemy.exc import IntegrityError
from datetime import datetime

import web.config
import traceback

from os.path import join

from .models import User

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()


# def load_config():
#     config_file = "config/jenkins.yml"
    # config_file = "../config/jenkins.yml"
    # fconfig = os.getenv('FLASK_CONFIG')

    # if fconfig:
    #     config_file = fconfig

    # config = configReader.read(config_file)
    # app.config.update(config)

    # sqlalechmy_db = "sqlite:///{}".format(config['db_path'])
    # app.config['SQLALCHEMY_DATABASE_URI'] = sqlalechmy_db


# load_config()


def get_data():
    return db.session.query(model.Multirun).all()


def create_eos_path(multirun):
    paths = []
    for dir in multirun.eos_dirs:
        # TODO: can be optimized a little bit
        path = app.config['eos_workspace_path']
        path = "{}/{}/{}/{}/".format(path, multirun.scram_arch, multirun.cmssw, dir.eos_dir)
        paths.append(path)
    return paths


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/test/')
def test():
    print get_data()
    return "response"


@app.route('/display/')
def display():
    multiruns = get_data()
    for multirun in multiruns:
        multirun.eos_dir = create_eos_path(multirun)
    return render_template('multirun_table.html', multiruns=multiruns)


if __name__ == '__main__':
    app.run()
