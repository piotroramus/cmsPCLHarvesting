import os
import sys

# in order to import higher level modules
sys.path.insert(1, os.path.join(sys.path[0], '..'))

import model

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../test.db'

db = SQLAlchemy(app)

def get_data():
    return db.session.query(model.Multirun).all()


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/display/')
def display():

    result = ""
    for multirun in get_data():
        result = "{}MID: {}\tDATASET: {}\n".format(result, multirun.id, multirun.dataset)
    return result


if __name__ == '__main__':
    app.run()
