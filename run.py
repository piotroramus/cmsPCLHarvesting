#!/usr/bin/env python

import os
import sys

from app import app
from keeperService import secretsDir

# from flask_script import Manager
# manager = Manager(app)

from app import service

if __name__ == "__main__":

    service._init()

    if not service.settings['listeningPort']:
        print "please specify a listening port (-p) ... "
        sys.exit(-1)

    # --- SSL
    PRIVATE_KEY_FILE = None
    CERTIFICATE_FILE = None
    if os.path.isfile(secretsDir + '/hostkey.pem'):
        PRIVATE_KEY_FILE = secretsDir + '/hostkey.pem'
    if os.path.isfile(secretsDir + '/hostcert.pem'):
        CERTIFICATE_FILE = secretsDir + '/hostcert.pem'

    context = None
    if PRIVATE_KEY_FILE and CERTIFICATE_FILE:
        context = (CERTIFICATE_FILE, PRIVATE_KEY_FILE)

    app.run(host='0.0.0.0', port=service.settings['listeningPort'], debug=app.config['DEBUG'], ssl_context=context)

    # if you have problems with the certifcates or other SSL related trouble, 
    # you can use this line instead:
    # app.run( host='0.0.0.0', port=service.settings['listeningPort'], debug=app.config['DEBUG'] )
