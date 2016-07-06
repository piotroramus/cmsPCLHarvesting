import os
import logging
import requests

import logs.logger as logs


class Tier0Api(object):
    def __init__(self):
        self.express_url = 'https://cmsweb.cern.ch/t0wmadatasvc/prod/express_config'
        self.stream_done_url = "https://cmsweb.cern.ch/t0wmadatasvc/prod/run_stream_done"
        self.session = requests.Session()
        request = requests.Request('GET', self.express_url)  # URL will be overwritten anyway
        self.request = self.session.prepare_request(request)
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        logs.setup_logging()
        self.logger = logging.getLogger(__name__)

    def process_request(self, url):
        self.request.url = url

        # at the moment the authorization is not required, but it might be in the future
        # this is the way to handle it
        cert = os.getenv('X509_USER_PROXY')
        response = self.session.send(self.request, verify=False, cert=(cert, cert))
        return response.json()

    def get_run_express_config(self, run_number):
        url = "{}?run={}".format(self.express_url, run_number)
        return self.process_request(url)

    def get_run_info(self, run_number):
        cfg = self.get_run_express_config(run_number)
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
            self.logger.debug('Express config not available for run {}'.format(run_number))
            return None

    def run_stream_completed(self, run_number):
        cfg = self.get_run_express_config(run_number)
        try:
            stream = cfg[u'result'][0][u'stream']
            stream_done_url = "{}?run={}&stream={}".format(self.stream_done_url, run_number, stream)
            result = self.process_request(stream_done_url)
            return result[u'result'][0]
        except IndexError:
            self.logger.debug('Cannot determine if stream is completed for run {}')
            return -1  # cannot return None, since in simple if it will be equal to False
