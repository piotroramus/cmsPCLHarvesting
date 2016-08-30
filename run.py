#!/usr/bin/env python

import os
import sys
import subprocess

from app import app
from keeperService import secretsDir

# from flask_script import Manager
# manager = Manager(app)

from app import service

if __name__ == "__main__":

    script_dir = os.path.dirname(os.path.realpath(__file__))
    kinit_path = "{}/kinit.sh".format(script_dir)
    subprocess.Popen([kinit_path])

    service._init()

    if not service.settings['listeningPort']:
        print "please specify a listening port (-p) ... "
        sys.exit(-1)

    # set up an SSL environment for secure access to your service:
    # from OpenSSL import SSL
    # context = SSL.Context(SSL.TLSv1_METHOD)
    # context.use_privatekey_file(secretsDir+'/hostkey.pem')
    # context.use_certificate_file(secretsDir+'/hostcert.pem')


    app.run( host='0.0.0.0', port=service.settings['listeningPort'], debug=app.config['DEBUG']) # , ssl_context=context)

    # if you have problems with the certifcates or other SSL related trouble, 
    # you can use this line instead:
    # app.run( host='0.0.0.0', port=service.settings['listeningPort'], debug=app.config['DEBUG'] )

