import os
import logging
import requests

import logs.logger as logs


class Tier0Api(object):
    def __init__(self):
        self.express_url = 'https://cmsweb.cern.ch/t0wmadatasvc/prod/express_config'
        self.stream_done_url = "https://cmsweb.cern.ch/t0wmadatasvc/prod/run_stream_done"
        self.fcsr_url = "https://cmsweb.cern.ch/t0wmadatasvc/prod/firstconditionsaferun"
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
        t0_configs = self.process_request(url)
        try:
            for t0_config in t0_configs[u'result']:
                if "Express" in t0_config[u'stream']:
                    return t0_config
        except KeyError:
            pass

        # returned here rather than in except part
        # because we want to handle the case when the for loop passes without return
        self.logger.error('Express config not available for run {}'.format(run_number))
        return None

    def get_run_info(self, run_number, job_config):
        express_config = self.get_run_express_config(run_number)
        if not express_config:
            return None
        try:
            result = dict()
            result['cmssw'] = express_config[u'reco_cmssw']
            result['scram_arch'] = express_config[u'reco_scram_arch']
            result['scenario'] = express_config[u'scenario']
            result['global_tag'] = express_config[u'global_tag']
            allowed_workflows = [x for x in job_config['workflows'].keys()]
            stream_workflows = express_config[u'alca_skim'].split(',')
            result['workflows'] = [w for w in stream_workflows if w in allowed_workflows]
            return result
        except KeyError:
            self.logger.error('Cannot parse express config for run {}'.format(run_number))
            return None

    def express_stream_completed(self, run_number):
        express_config = self.get_run_express_config(run_number)
        if not express_config:
            # cannot return None, since in simple if it will be equal to False
            # and eventually after few days the stream will be treated as completed
            return -1
        try:
            stream = express_config[u'stream']
            stream_done_url = "{}?run={}&stream={}".format(self.stream_done_url, run_number, stream)
            result = self.process_request(stream_done_url)
            return result[u'result'][0]
        except IndexError:
            self.logger.debug('Cannot determine if stream is completed for run {}')
            return -1
