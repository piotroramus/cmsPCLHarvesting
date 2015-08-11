__author__ = 'ap'

import socket
import os
import sys

secretsDir = os.path.abspath( os.path.join( '/data', 'secrets'))
if not os.path.exists(secretsDir):  # not an official installation, look for it in a relative path:
    secretsDir = os.path.abspath( os.path.join( os.path.dirname(__file__), '..', 'secrets'))

if secretsDir not in sys.path:
    sys.path.append(secretsDir)

print "in ", os.getcwd(), 'secrets from ', secretsDir

from secrets import secrets

serviceName = 'myService'

def getEncryptionString():
    return secrets[serviceName]['encString']

def getConnections( dbName ):
    connString = secrets[serviceName]['connections'][getProductionLevel()][dbName]
    # print '==> ', connString
    return makeConnString( connString )

def makeConnString(connection_string):

    if not isinstance(connection_string, str): # got a dict ....
        if 'sqlite' in connection_string['db_name']:
            if connection_string['db_name'].startswith('sqlite:////'):
                connection_string = connection_string['db_name']  # return the given absolute path
            else:
                connection_string = 'sqlite:///'+os.path.join('/',
                                                              os.path.abspath(os.path.dirname(__file__)),
                                                              connection_string['db_name'].replace('sqlite:///', ''))
                print "conn:", connection_string
        else:
           connection_string = 'oracle://%s:%s@%s' % (
                connection_string['user'],
                connection_string['password'],
                connection_string['db_name'],
            )

    return connection_string

productionLevels = {
    'vocms0150.cern.ch': 'test',
    'vocms0145.cern.ch': 'dev',
    'vocms0146.cern.ch': 'int',
    'vocms0226.cern.ch': 'pro',
}

def getProductionLevel(hostName = None):
    '''Returns the production level given a hostname (or current hostname by default). If the hostname is not found, returns 'private'.
    '''

    if not hostName:
        hostName = socket.gethostname()

    level = 'private'
    try:
        level = productionLevels[hostName]
    except:
        pass

    return level
