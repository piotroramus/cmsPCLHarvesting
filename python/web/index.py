import os
import sys

# in order to import 'higher' level modules
sys.path.insert(1, os.path.join(sys.path[0], '..'))

import model
import utils.configReader as configReader

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


def load_config():
    config_file = "../config/jenkins.yml"
    fconfig = os.getenv('FLASK_CONFIG')

    if fconfig:
        config_file = fconfig

    config = configReader.read(config_file)
    app.config.update(config)

    sqlalechmy_db = "sqlite:///{}".format(config['db_path'])
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlalechmy_db


load_config()
db = SQLAlchemy(app)


def get_data():
    return db.session.query(model.Multirun).all()


def create_eos_path(multirun):
    path = None
    if multirun.eos_dir:
        path = app.config['eos_workspace_path']
        path = "{}/{}/{}/{}/".format(path, multirun.scram_arch, multirun.cmssw, multirun.eos_dir)
    return path


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
