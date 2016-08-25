import logging

from rrapi.rrapi_v4 import RhApi
from rrapi.rrapi_v3 import RRApi, RRApiError
import logs.logger as logs


class RRApiWrapper(object):
    def __init__(self, config):
        self.config = config
        self.rrapi = RhApi(config['rrapi_url'], debug=False)
        logs.setup_logging()
        self.logger = logging.getLogger(__name__)

    def query(self, days_old_runs_date, run_class_names):

        if self.config['use_rrapi_v3']:
            return self._query_v3(days_old_runs_date, run_class_names)

        self.logger.info("Using RunRegistry API v4")
        filters = "where r.starttime > TO_DATE('{}', 'YYYY-MM-DD')".format(days_old_runs_date)
        filters += " and (r.run_class_name = {})".format(
            " or r.run_class_name = ".join("'" + cn + "'" for cn in run_class_names))
        query = "select r.runnumber, r.run_class_name, r.starttime, r.bfield from runreg_global.runs r {}".format(
            filters)

        self.logger.info("Fetching Run Registry records from last {} days".format(self.config['days_old_runs']))
        recent_runs = self.rrapi.json2(query)[u'data']

        return recent_runs

    def _query_v3(self, days_old_runs_date, run_class_names):

        import datetime

        self.logger.info("Using RunRegistry API v3")
        self.rrapi = RRApi(self.config['rrapiv3_url'], debug=False)

        filters = dict()
        filters['runClassName'] = "= {}".format(' or = '.join(run_class_names))
        filters['startTime'] = "> {}".format(days_old_runs_date)

        recent_runs = []
        try:
            self.logger.info("Fetching Run Registry records from last {} days".format(self.config['days_old_runs']))
            recent_runs = self.rrapi.data(
                workspace='GLOBAL',
                columns=['number', 'startTime', 'runClassName', 'bfield'],
                table='runsummary',
                template='json',
                filter=filters
            )
        except RRApiError:
            self.logger.error("Error while querying RR API for {} days old runs".format(self.config['days_old_runs']),
                              exc_info=True)

        # convert results to the same format as v4 so the 'API' is not broken
        result = []
        for run in recent_runs:
            r = {}
            r[u'runnumber'] = run[u'number']
            r[u'starttime'] = datetime.datetime.strptime(run[u'startTime'], "%a %d-%m-%y %H:%M:%S") \
                .strftime("%Y-%m-%d %H:%M:%S")
            r[u'runClassName'] = run[u'runClassName']
            r[u'bfield'] = run[u'bfield']
            result.append(r)

        return result
