import os
import httplib
import json


class DBSApi(object):
    """ Tailored version of DBSApi.
        Does not require pycurl which was very problematic.
        Based on https://github.com/cms-PdmV/wmcontrol/blob/master/modules/wma.py

        In order to authenticate, X509_USER_PROXY environment variable needs to be set.
        It can be obtained the following way:

        # get proxy certificate
        voms-proxy-init -rfc -voms cms
        # set variable
        export X509_USER_PROXY=$(voms-proxy-info --path)

    """

    def __init__(self, dbs3url='/dbs/prod/global/DBSReader/'):
        self.connection = None
        self.connection_attempts = 3
        self.wmagenturl = 'cmsweb.cern.ch'
        self.dbs3url = dbs3url

    def _abort(self, reason=""):
        raise Exception("Something went wrong. Aborting. {}".format(reason))

    def _init_connection(self, url):
        return httplib.HTTPSConnection(url, port=443,
                                       cert_file=os.getenv('X509_USER_PROXY'),
                                       key_file=os.getenv('X509_USER_PROXY'))

    def _refresh_connection(self, url):
        self.connection = self._init_connection(url)

    def _build_params_query(self, params):
        params_query = ""
        for key in params:
            params_query = "{}&{}={}".format(params_query, key, params[key])
        if params_query.startswith('&'):
            params_query = params_query[1:]
        return params_query

    def _api(self, method, params):
        """Constructs query and returns DBS3 response
        """
        if not self.connection:
            self._refresh_connection(self.wmagenturl)

        # this way saves time for creating connection per every request
        query = None
        result = None
        for i in range(self.connection_attempts):
            try:
                params_query = self._build_params_query(params)
                query = self.dbs3url + "{}?{}".format(method, params_query)
                result = self._httpget(self.connection, query)
                break
            except Exception:
                # most likely connection terminated
                self._refresh_connection(self.wmagenturl)
        try:
            return json.loads(result)
        except:
            self._abort("Could not load the answer from DBS3: {}".format(query))

    def _httpget(self, conn, query):
        conn.request("GET", query.replace('#', '%23'))
        try:
            response = conn.getresponse()
        except httplib.BadStatusLine:
            raise RuntimeError('Something is really wrong')
        if response.status != 200:
            print "Problems quering DBS3 RESTAPI with {}: {}".format(query.replace('#', '%23'), response.read())
            return None
        return response.read()

    def listDatasets(self, run_num, dataset):
        params = {
            'run_num': run_num,
            'dataset': dataset
        }
        return self._api('datasets', params)

    def listBlocks(self, run_num, dataset):
        params = {
            'run_num': run_num,
            'dataset': dataset
        }
        return self._api('blocks', params)

    def listFiles(self, run_num, block_name):
        params = {
            'run_num': run_num,
            'block_name': block_name
        }
        return self._api('files', params)

    def listFileSummaries(self, run_num, block_name):
        params = {
            'run_num': run_num,
            'block_name': block_name
        }
        return self._api('filesummaries', params)
