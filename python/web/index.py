import os
import sys

# in order to import 'higher' level modules
sys.path.insert(1, os.path.join(sys.path[0], '..'))

import model
import utils.configReader as configReader

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


def load_config():
    config_file = "../config/local.yml"
    fconfig = os.getenv('FLASK_CONFIG')

    if fconfig:
        config_file = fconfig

    config = configReader.read(config_file)
    app.config.update(config)

    # sqlalechmy_db = "sqlite:///{}.db".format(config['db_path'])
    sqlalechmy_db = "sqlite:///../{}.db".format(config['db_path'])
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlalechmy_db


load_config()
db = SQLAlchemy(app)


def get_data():
    return db.session.query(model.Multirun).all()


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/test/')
def test():
    return "response"


@app.route('/display/')
def display():
    result = ""
    for multirun in get_data():
        result = "{}MID: {}\tDATASET: {}\n".format(result, multirun.id, multirun.dataset)
    return result


if __name__ == '__main__':
    app.run()
