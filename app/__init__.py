
# import the ldapAuth here (before the flask stuff) to avoid the
# LDAPError: (2, 'No such file or directory')
# which is caused by some issue inside ldap when accessing ssl.
from app import ldapAuth

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api
from flask_sslify import SSLify

import os

import logging
from logging.handlers import RotatingFileHandler

from config import config

app = Flask(__name__)
app.config.from_object(config['default'])

db = SQLAlchemy(app)
auth = HTTPBasicAuth()
api = Api(app)

sslify = SSLify(app)

#logging
if not os.path.exists( app.config['LOGGING_DIR'] ):
    os.makedirs( app.config['LOGGING_DIR'] )
handler = RotatingFileHandler(app.config['LOGGING_FILE'], maxBytes=1 * 1024 * 1024, backupCount=10)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))

app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.info('service startup')

# business logic comes here ... 

from app import routes

