
__author__ = 'andreas.pfeiffer@cern.ch'

from datetime import datetime

# from ldap3_manager import authenticate, userInGroup
from .ldapAuth import authenticate, userInGroup

from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

from flask import current_app

from . import db

class User(db.Model):
    __tablename__ = 'users'
    __bind_key__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    def verify_password(self, password):
        dropboxGroup = 'cms-cond-dropbox'
        current_app.logger.debug('going to authenticate user %s ', self.username)
        status, errString = authenticate(self.username, password)
        if not status:
            current_app.logger.error('when authenticating user %s:%s', self.username, errString)

        if not userInGroup(self.username, dropboxGroup):
            current_app.logger.error('user %s not found in group %s', self.username, dropboxGroup)
            status = False # flag not authorised ...
        current_app.logger.debug('user %s authenticated and found to be in eGroup %s', self.username, dropboxGroup)
        return status

    def generate_auth_token(self, expiration=600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user

# other Model classes go here ... 

