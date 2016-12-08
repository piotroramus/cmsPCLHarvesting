import os
import sqlalchemy
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath('../../python'))

import model
from dataDiscovery import discover
from t0wmadatasvcApi.t0wmadatasvcApi import Tier0Api


class LoggerMock(object):
    def __init__(self, level):
        self.available_levels = {
            "DEBUG": 1,
            "INFO": 2,
            "WARNING": 3,
            "ERROR": 4
        }
        if level not in self.available_levels:
            raise ValueError('Invalid logging level')
        self.level = self.available_levels[level]
        self.messages = dict()
        self.reset()

    def debug(self, msg):
        if self.level <= self.available_levels["DEBUG"]:
            self.messages["DEBUG"].append(msg)

    def info(self, msg):
        if self.level <= self.available_levels["INFO"]:
            self.messages["INFO"].append(msg)

    def warning(self, msg):
        if self.level <= self.available_levels["WARNING"]:
            self.messages["WARNING"].append(msg)

    def error(self, msg):
        if self.level <= self.available_levels["ERROR"]:
            self.messages["ERROR"].append(msg)

    def reset(self):
        for lvl in self.available_levels:
            self.messages[lvl] = []


class OrderedLoggerMock(LoggerMock):
    def __init__(self, level):
        super(OrderedLoggerMock, self).__init__(level)
        self.msg_number = 1

    def debug(self, msg):
        if self.level <= self.available_levels["DEBUG"]:
            self.messages["DEBUG"].append((self.msg_number, msg))
            self.msg_number += 1

    def info(self, msg):
        if self.level <= self.available_levels["INFO"]:
            self.messages["INFO"].append((self.msg_number, msg))
            self.msg_number += 1

    def warning(self, msg):
        if self.level <= self.available_levels["WARNING"]:
            self.messages["WARNING"].append((self.msg_number, msg))
            self.msg_number += 1

    def error(self, msg):
        if self.level <= self.available_levels["ERROR"]:
            self.messages["ERROR"].append((self.msg_number, msg))
            self.msg_number += 1

    def reset(self):
        super(OrderedLoggerMock, self).reset()
        self.msg_number = 1


class T0ApiStreamAlwaysCompleted(Tier0Api):
    def express_stream_completed(self, run_number):
        return True


class T0ApiStreamNeverCompleted(Tier0Api):
    def express_stream_completed(self, run_number):
        return False


class DiscoverTest(unittest.TestCase):
    def test_discover(self):
        pass

    def test_get_base_release(self):
        valid_releases = [
            'CMSSW_8_0_10',
            "CMSSW_9_1_1",
            "CMSSW_10_0_11",
            "CMSSW_8_0_8_patch1"
        ]

        for release in valid_releases:
            # assert the functions does not raise an exception
            discover.get_base_release(release)

        invalid_releases = [
            'CMSSW_',
            'CMSSW_808'
            'abd',
            'CMSSW_a_0_11',
            'CMSSW_8_0_tt',
            'CMSSW_10_a_12'
            'CMSSW_8_0_8a',
            'CMSSW_8_00',
            'aCMSSW_8_0_10'
        ]

        for release in invalid_releases:
            self.assertRaises(ValueError, discover.get_base_release, release)

        release = 'CMSSW_8_0_8'
        self.assertEqual(discover.get_base_release(release), 'CMSSW_8_0_')
        release = 'CMSSW_8_0_8_patch1'
        self.assertEqual(discover.get_base_release(release), 'CMSSW_8_0_')
        release = 'CMSSW_10_1_8'
        self.assertEqual(discover.get_base_release(release), 'CMSSW_10_1_')
        release = 'CMSSW_7_0_24324'
        self.assertEqual(discover.get_base_release(release), 'CMSSW_7_0_')

        # TODO: this has been moved to utils and the test needs to be moved as well
        # def test_get_run_class_names(self):
        #     workflow_run_classes = {'PromptCalibProdSiStripGains': ['Collisions15', 'Collisions16'],
        #                             'PromptCalibProdSiStrip': ['Collisions15', 'Collisions16'],
        #                             'PromptCalibProdSiPixelAli': ['Collisions15', 'Collisions16'],
        #                             'PromptCalibProdSiStripGainsAfterAbortGap': ['Collisions16'],
        #                             'PromptCalibProd': ['Collisions15', 'Collisions16']}

        # expected_result = {'Collisions15', 'Collisions16'}
        # run_class_names = discover.get_run_class_names(workflow_run_classes)
        # self.assertEqual(run_class_names, expected_result)

        # imaginary_workflow_run_classes = {'PromptCalibProdSiStripGains': ['Collisions15', 'A'],
        #                                   'PromptCalibProdSiStrip': ['ILOVE_CMS', 'Collisions16', 'B', 'C'],
        #                                   'RandomWorkflow': ['Collisions15', 'A'],
        #                                   'PromptCalibProd': ['E', 'Collisions16']}

        # expected_result = {'Collisions15', 'Collisions16', 'A', 'B', 'C', 'E', 'ILOVE_CMS'}
        # run_class_names = discover.get_run_class_names(imaginary_workflow_run_classes)
        # self.assertEqual(run_class_names, expected_result)


class UpdateRunsTest(unittest.TestCase):
    def setUp(self):
        date = time.strftime("%d-%m-%Y_%H.%M.%S")
        self.database_file = "test-{}.db".format(date)
        connection_string = "sqlite:///{}".format(self.database_file)
        engine = sqlalchemy.create_engine(connection_string, echo=False)
        model.Base.metadata.create_all(engine, checkfirst=True)
        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        self.session = Session()
        self.logger = OrderedLoggerMock('DEBUG')

        self.t0api_stream_completed = T0ApiStreamAlwaysCompleted()
        self.t0api_stream_not_completed = T0ApiStreamNeverCompleted()

        self.__init_db()

    def __init_db(self):
        ri = model.RunInfo()
        ri.stream_completed = True
        ri.stream_timeout = False
        self.session.add(ri)
        self.session.commit()

    def tearDown(self):
        os.remove(self.database_file)
        # pass

    def get_local_runs(self):
        pass

    def get_recent_runs(self):
        pass

    def test_run_becoming_completed(self):
        pass

    def test_no_new_runs(self):
        run1 = model.RunInfo()
        run1.number = 1
        run1.stream_completed = True

        run2 = model.RunInfo()
        run2.number = 2
        run2.stream_completed = True

        run3 = model.RunInfo()
        run3.number = 3
        run3.stream_completed = True

        recent_run1 = {
            u'runnumber': 1,
            u'starttime': u'2016-08-11 10:35:56'
        }
        recent_run2 = {
            u'runnumber': 2,
            u'starttime': u'2016-08-11 12:35:56'
        }
        recent_run3 = {
            u'runnumber': 3,
            u'starttime': u'2016-08-11 14:35:56'
        }

        config = {"run_stream_timeout": 5}
        local_runs = [run1, run2, run3]
        recent_runs = [recent_run1, recent_run2, recent_run3]

        discover.update_runs(self.logger, self.session, self.t0api_stream_completed, config, local_runs, recent_runs)

        # it is hard to determine the results itself so the test focuses on the right processing flow
        expected_info_logs = [
            (1, 'Updating local database with newly fetched runs'),
            (2, 'Checking run 1 fetched from Run Registry'),
            (3, 'Run 1 already exists in local database'),
            (4, 'Checking run 2 fetched from Run Registry'),
            (5, 'Run 2 already exists in local database'),
            (6, 'Checking run 3 fetched from Run Registry'),
            (7, 'Run 3 already exists in local database')
        ]

        output_info_logs = self.logger.messages['INFO']
        self.assertEqual(expected_info_logs, output_info_logs)


if __name__ == '__main__':
    unittest.main()
