'''Common code for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import re
import os
import sys
import optparse
import logging
import unittest
import json
import base64
import time
import datetime
import netrc
import xml.sax.saxutils
import xml.dom.minidom

secretsPath = os.getcwd()+'/../secrets'
if secretsPath not in sys.path:
    sys.path.append(secretsPath)

settings = None
secrets = None

def _init():
    '''Setup 'settings' and 'secrets' global variables by parsing
    the command line options.
    '''

    parser = optparse.OptionParser()

    parser.add_option('-n', '--name', type = 'str',
        dest = 'name',
        help = 'The name of the service.'
    )

    parser.add_option('-r', '--rootDirectory', type = 'str',
        dest = 'rootDirectory',
        help = 'The root directory for the service.'
    )

    parser.add_option('-s', '--secretsDirectory', type = 'str',
        dest = 'secretsDirectory',
        help = 'The shared secrets directory.'
    )

    parser.add_option('-p', '--listeningPort', type = 'int',
        dest = 'listeningPort',
        help = 'The port this service will listen to.'
    )

    parser.add_option('-l', '--productionLevel', type = 'str',
        dest = 'productionLevel',
        help = 'The production level this service should run as, which can be one of the following: "dev" == Development, "int" == Integration, "pro" == Production. For instance, the service should use this parameter to decide to which database connect, to which mailing list should send emails, etc.'
    )

    parser.add_option('-c', '--caches', type = 'str',
        dest = 'caches',
        help = 'The cache to ID mapping of the caches that the service uses.'
    )

    options = parser.parse_args()[0]

    # Set the settings
    global settings
    cacheDict = {}
    try:
        cacheDict = dict([(str(x[0]), x[1]) for x in json.loads(options.caches).items()])
    except TypeError:
        pass
    settings = {
        'name': options.name,
        'rootDirectory': options.rootDirectory,
        'secretsDirectory': options.secretsDirectory,
        'listeningPort': options.listeningPort,
        'productionLevel': options.productionLevel,
        'caches': cacheDict,
    }
    if not options.name:
        settings['name'] = 'condUploader'

    # Set the secrets
    global secrets
    import secrets
    if settings['name'] in secrets.secrets:
        secrets = secrets.secrets[settings['name']]
    else:
        secrets = secrets.secrets

    logLevel = logging.INFO
    if settings['productionLevel'] == 'private':
        logLevel = logging.DEBUG

    # Initialize the logging module with a common format
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logLevel
    )

_init()



# Hostname and URL related functions

def getHostname():
    '''Returns the 'official' hostname where services are run.

    In private deployments, this is the current hostname. However,
    in official ones, could be, for instance, a DNS alias.

    e.g. cms-conddb-dev.cern.ch
    '''

    hostnameByLevel = {
        'pro': 'cms-conddb-prod.cern.ch',
        'int': 'cms-conddb-int.cern.ch',
        'dev': 'cms-conddb-dev.cern.ch',
        # 'dev': 'cms-conddb-test.cern.ch',
        'private': socket.getfqdn(),
    }

    return hostnameByLevel[settings['productionLevel']]


def getBaseURL():
    '''Returns the base URL for all the services (without trailing slash).

    The hostname is the one returned by getHostname(), so the same notes
    regarding the returned hostname apply here.

    e.g. https://cms-conddb-dev.cern.ch
    '''

    return 'https://%s' % getHostname()


def getURL():
    '''Returns the URL of the service (without trailing slash).

    The base URL is the one returned by getBaseURL(), so the same notes
    regarding the returned hostname apply here.

    e.g. https://cms-conddb-dev.cern.ch/docs
    '''

    return '%s/%s' % (getBaseURL(), settings['name'])


# Utility functions

def makePath(path):
    '''Makes directories in the path if they do not exist yet.

    Like os.makedirs() but without failing if the exist.

    Note that this function has a race condition, so do not use it
    from multiple callers at the same time.
    '''

    if not os.path.exists(path):
        logging.debug('%s: Creating path...', path)
        os.makedirs(path)


def getFilesPath():
    '''Returns the path to the files folder where a service can store
    permanent files (but local to the backend machine).
    '''

    return os.path.join('/data/files', settings['name'])


def onlyPrivate(f):
    '''Decorator that only defines a function if the productionLevel
    is private.

    Useful to have testing methods in CherryPy, only available
    in private instances.
    '''

    if settings['productionLevel'] == 'private':
        return f


def getPrettifiedJSON(data, sortKeys = True):
    '''Returns prettified JSON (valid and easily read JSON).
    '''

    return json.dumps(data, sort_keys = sortKeys, indent = 4, default = lambda obj: obj.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3] if isinstance(obj, datetime.datetime) else None)


def escape(x):
    '''Escapes data for XML/HTML.
    '''

    tx = type(x)

    if x is None or tx in (bool, int, long):
        return x

    if tx in (str, unicode):
        return xml.sax.saxutils.escape(x)

    if tx in (list, tuple):
        return [escape(y) for y in x]

    if tx in (set, frozenset):
        ret = set([])
        for y in x:
            ret.add(escape(y))
        return ret

    if tx == dict:
        for y in x.items():
            x[y[0]] = escape(y[1])
        return x

    if tx == datetime.datetime:
        return x.replace(microsecond = 0)

    raise Exception('escape(): Type %s not recognized.' % str(type(x)))


def _getPIDs(string):
    '''Returns the PIDs matching the string, without grep nor bash.
    '''

    return os.popen("ps auxww | grep -F '" + string + "' | grep -F 'python' | grep -F -v 'grep' | grep -F -v 'bash' | awk '{print $2}'", 'r').read().splitlines()


def isAnotherInstanceRunning():
    '''Returns whether another instance of the script is running.
    '''

    return len(_getPIDs(sys.argv[0])) > 1


# Functions for generating connection strings and URLs

def getConnectionDictionaryFromNetrc(entry):
    '''Returns a connection dictionary from a netrc entry.
    (intended for personal/private database accounts and the like, instead
    of the normal production ones from the secrets file).
    '''

    try:
        (user, db_name, password) = netrc.netrc().authenticators(entry)
    except TypeError:
        raise Exception('netrc entry %s could not be found.' % entry)

    return  {
        'user': user,
        'password': password,
        'db_name': db_name,
    }


def getOracleConnectionString(connectionDictionary):
    '''Returns a connection string for Oracle given
    a connection dictionary from the secrets file.
    '''

    return 'oracle://%s/%s' % (connectionDictionary['db_name'], connectionDictionary['account'])


def getCxOracleConnectionString(connectionDictionary):
    '''Returns a connection string for cx_oracle given
    a connection dictionary from the secrets file.
    '''

    return '%s/%s@%s' % (connectionDictionary['user'], connectionDictionary['password'], connectionDictionary['db_name'])


def getSqlAlchemyConnectionString(connectionDictionary):
    '''Returns a connection string for SQL Alchemy given
    a connection dictionary from the secrets file.
    '''

    return 'oracle://%s:%s@%s' % (connectionDictionary['user'], connectionDictionary['password'], connectionDictionary['db_name'])


frontierConnectionStringTemplate = None
def getFrontierConnectionString(connectionDictionary, short = False):
    '''Returns a connection string for Frontier given
    a connection dictionary from the secrets file.
    '''

    if short:
        return 'frontier://%s/%s' % (connectionDictionary['frontier_name'], connectionDictionary['account'])

    global frontierConnectionStringTemplate
    if frontierConnectionStringTemplate is None:
        siteLocalConfigFilename = '/afs/cern.ch/cms/SITECONF/CERN/JobConfig/site-local-config.xml'

        frontierName = ''
        dom = xml.dom.minidom.parse(siteLocalConfigFilename)
        nodes = dom.getElementsByTagName('frontier-connect')[0].childNodes
        for node in nodes:
            if node.nodeType in frozenset([xml.dom.minidom.Node.TEXT_NODE, xml.dom.minidom.Node.COMMENT_NODE]):
                continue

            if node.tagName == 'proxy':
                frontierName += '(proxyurl=%s)' % str(node.attributes['url'].nodeValue)

            if node.tagName == 'server':
                # Override the frontier name
                frontierName += '(serverurl=%s/%s)' % (str(node.attributes['url'].nodeValue).rsplit('/', 1)[0], '%s')

        dom.unlink()

        frontierConnectionStringTemplate = 'frontier://%s/%s' % (frontierName, '%s')

    return frontierConnectionStringTemplate % ((frontierConnectionStringTemplate.count('%s') - 1) * (connectionDictionary['frontier_name'], ) + (connectionDictionary['account'], ))


def getProtocolServiceAndAccountFromConnectionString(connectionString):
    '''Extract the protocol, the service and the account name from a given connection string.
    Parameters:
    connectionString: the input connection string.
    @returns: a dictionary in the form {'protocol' : protocol_name, 'service' : service_name, 'account' : account_name}, None if parsing error'''

    protocol, serviceAndAccount = connectionString.partition( '://' )[ : : 2 ]
    logging.info("gPSaAfCS-1] ==> got %s, %s", protocol, serviceAndAccount)
    if protocol != 'frontier' and protocol != 'oracle': #the supported protocols are frontier and oracle
        return None
    serviceConfiguration, account = serviceAndAccount.rpartition( '/' )[ : : 2 ]
    logging.info('gPSaAfCS-2] ==> got svcCfg: "%s", account "%s" ', serviceConfiguration, account)
    if account == '' or serviceConfiguration == '': #only protocol provided (serviceAndAccount empty, so account and service both empty), or no account provided, but service ends with (account empty) or without (service empty) a /
        logging.info('gPSaAfCS-3] ==> complex, see code')
        return None
    if serviceConfiguration.count( '/' ) > 1 and serviceConfiguration.count( '(' ) == 0: #too many slashes, but no explicit configuration
        logging.info('gPSaAfCS-3] ==> too many slashes but no explicit config')
        return None
    if serviceConfiguration.count( '/' ) == 0: #no server and proxies specified, but other configurations can be there after the service name
        service = serviceConfiguration.partition( '(' )[ 0 ]
    elif serviceConfiguration.count( '/' ) == 1: #only one instance of the server address was provided
        service = serviceConfiguration.partition( '/' )[ 2 ]
    else: #it is a long connection string: find all the serverurl parameter
        tempStr = serviceConfiguration
        service = ''
        for _ in xrange( serviceConfiguration.count( "serverurl=" ) ):
            servletURL = tempStr[ tempStr.find( "serverurl=" ) + len( "serverurl=" ) : tempStr.find( ')', tempStr.find( "serverurl=" ) ) ]
            newServlet = servletURL.rpartition( '/' )[ -1 ]
            if service == '':
                service = newServlet
            elif service != newServlet: # there can be only one servlet, otherwise the connection string is malformed
                return None
            tempStr = tempStr[ tempStr.find( ')', tempStr.find( "serverurl=" ) ) + len( ')' ) : ]
    ret = {'protocol' : protocol, 'service' : service, 'account' : account}
    logging.debug('gPSaAfCS-3] ==> returning %s', str(ret))
    return ret


def getFrontierConnectionStringList(connectionsDictionary):
    '''Returns a list of connection strings for Frontier given
    a connections dictionary with multiple accounts from the secrets file.
    '''

    connectionStringList = []

    for account in connectionsDictionary['accounts']:
        connectionStringList.append(getFrontierConnectionString({
            'account': account,
            'frontier_name': connectionsDictionary['frontier_name']
        }))

    return connectionStringList

def getWinServicesSoapBaseUrl(connectionDictionary):
    '''Returns a winservices-soap base URL given a connection dictionary
    from the secrets file.
    '''

    return 'https://winservices-soap.web.cern.ch/winservices-soap/Generic/Authentication.asmx/'

import httplib, ssl, urllib2, socket
class HTTPSConnectionTLS(httplib.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        httplib.HTTPSConnection.__init__(self, *args, **kwargs)

    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        try:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_TLSv1)
        except ssl.SSLError, e:
            print("Trying TLSv1.")
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_TLSv1)

class HTTPSHandlerTLS(urllib2.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(HTTPSConnectionTLS, req)

# install opener
urllib2.install_opener(urllib2.build_opener(HTTPSHandlerTLS()))

def winServicesSoapSignIn(winServicesUrl, username, password):
    try:
        connectionDictionary = secrets['winservices']
        url = '%sGetUserInfo?UserName=%s&Password=%s' % (winServicesUrl, username, password)

        logging.debug( "using %s for auth to %s", connectionDictionary['user'], url[:url.find('?')] )

        request = urllib2.Request( url )
        # You need the replace to handle encodestring adding a trailing newline
        # (https://docs.python.org/2/library/base64.html#base64.encodestring)
        base64string = base64.encodestring( '%s:%s' % (connectionDictionary['user'], connectionDictionary['password']) ).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)

        data = urllib2.urlopen( request ).read()
        status = int(data[data.find('</auth>') - 1])

        # Status codes:
        #   0 == Account disabled or activation pending or expired
        #   1 == Invalid password
        #   2 == Incorrect login or E-mail
        #   3 == Success
        #   4 == Success but not in eGroup
        success = 3
        if status == success or status == 4:
            return True
    except Exception as e:
        logging.error('winServicesSoapSignIn(): %s\n - url:%s\n - username:%s', e, winServicesUrl+'GetUserInfo', username)

    return False


def winServicesSoapIsUserInGroup(winServicesUrl, username, group):
    try:
        connectionDictionary = secrets['winservices']
        url = '%sUserIsMemberOfGroup?UserName=%s&GroupName=%s' % (winServicesUrl, username, group)

        logging.debug( "using %s for auth to %s", connectionDictionary['user'], url[:url.find('?')] )

        request = urllib2.Request( url )
        # You need the replace to handle encodestring adding a trailing newline
        # (https://docs.python.org/2/library/base64.html#base64.encodestring)
        base64string = base64.encodestring( '%s:%s' % (connectionDictionary['user'], connectionDictionary['password']) ).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)

        # GetGroupsForUser does not return groups that are included in user's groups
        data = urllib2.urlopen( request ).read()
        return re.search('<boolean.*>true</boolean>', data) is not None
    except Exception as e:
        logging.error('isUserInGroup(): %s', e)

    return False


# Functions for testing

def parseCherryPyErrorPage(errorPage):
    return errorPage.split('<p>')[1].split('</p>')[0]



def setupTest():
    logging.getLogger().setLevel(logging.INFO)


def test(TestCase):
    setupTest()
    return not unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(TestCase)).wasSuccessful()


class TestCase(unittest.TestCase):
    '''An specialized TestCase for our services.
    '''

    warningTime = 4. # seconds

    def __init__(self, methodName = 'runTest'):
        super(TestCase, self).__init__(methodName)


    def setUp(self):
        self.startTime = time.time()


    def tearDown(self):
        totalTime = time.time() - self.startTime
        if totalTime > self.warningTime:
            logging.warning('%s took %.2f seconds.', self.id(), totalTime)
