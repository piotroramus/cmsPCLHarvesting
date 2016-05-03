import os
import logging

from requests import Request, Session
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings

from logs.logger import setup_logging


class Tier0Api(object):
    def __init__(self):
        self.base_url = 'https://cmsweb.cern.ch/t0wmadatasvc/prod/express_config'
        self.session = Session()
        request = Request('GET', self.base_url)
        self.request = self.session.prepare_request(request)
        disable_warnings(InsecureRequestWarning)
        setup_logging()
        self.logger = logging.getLogger(__name__)

    def get_run_express_config(self, run):
        url = self.base_url + '?run=' + str(run)
        self.request.url = url

        # at the moment the authorization is not required, but it might be in the future
        # this is the way to handle it
        cert = os.getenv('X509_USER_PROXY')
        response = self.session.send(self.request, verify=False, cert=(cert, cert))
        return response.json()

    def get_run_info(self, run):
        cfg = self.get_run_express_config(run)
        try:
            result = dict()
            result['cmssw'] = cfg[u'result'][0][u'reco_cmssw']
            result['scram_arch'] = cfg[u'result'][0][u'reco_scram_arch']
            result['scenario'] = cfg[u'result'][0][u'scenario']
            result['global_tag'] = cfg[u'result'][0][u'global_tag']
            workflows = cfg[u'result'][0][u'alca_skim'].split(',')
            result['workflows'] = [w for w in workflows if w.startswith('PromptCalibProd')]
            return result
        except (KeyError, IndexError):
            self.logger.debug('Express config not available for run {}'.format(run))
            return None
