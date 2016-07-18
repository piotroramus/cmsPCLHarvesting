import logging

from rrapi.rrapi_v4 import RhApi
import logs.logger as logs


class RRApiWrapper(object):
    def __init__(self, config):
        self.config = config
        self.rrapi = RhApi(config['rrapi_url'], debug=False)
        logs.setup_logging()
        self.logger = logging.getLogger(__name__)

    def query(self, days_old_runs_date, run_class_names):
        filters = "where r.starttime > TO_DATE('{}', 'YYYY-MM-DD')".format(days_old_runs_date)
        filters += " and (r.run_class_name = {})".format(
            " or r.run_class_name = ".join("'" + cn + "'" for cn in run_class_names))
        query = "select r.runnumber, r.run_class_name, r.starttime, r.bfield from runreg_global.runs r {}".format(
            filters)

        self.logger.info("Fetching Run Registry records from last {} days".format(self.config['days_old_runs']))
        recent_runs = self.rrapi.json2(query)[u'data']

        return recent_runs
