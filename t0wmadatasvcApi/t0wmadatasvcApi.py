import os
from requests import Request, Session
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings


class Tier0Api(object):
    def __init__(self):
        self.base_url = 'https://cmsweb.cern.ch/t0wmadatasvc/prod/express_config'
        self.session = Session()
        disable_warnings(InsecureRequestWarning)
        request = Request('GET', self.base_url)
        self.request = self.session.prepare_request(request)

    def get_run_express_config(self, run):
        url = self.base_url + '?run=' + str(run)
        self.request.url = url

        # at the moment the authorization is not required, but it might be in the future
        # this is the way to handle it
        cert = os.getenv('X509_USER_PROXY')
        response = self.session.send(self.request, verify=False, cert=(cert, cert))
        return response.json()

    def get_run_release(self, run):
        info = self.get_run_express_config(run)
        return info[u'result'][0][u'reco_cmssw']

