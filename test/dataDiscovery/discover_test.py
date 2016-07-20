import os
import sqlalchemy
import sys
import time
import unittest

from sqlalchemy.ext.declarative import declarative_base

sys.path.insert(0, os.path.abspath('../../python'))

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

    def debug(self, msg):
        if self.level <= self.available_levels["DEBUG"]:
            print msg

    def info(self, msg):
        if self.level <= self.available_levels["INFO"]:
            print msg

    def warning(self, msg):
        if self.level <= self.available_levels["WARNING"]:
            print msg

    def error(self, msg):
        if self.level <= self.available_levels["ERROR"]:
            print msg


class T0ApiStreamAlwaysCompleted(Tier0Api):
    def run_stream_completed(self, run_number):
        return True


class T0ApiStreamNeverCompleted(Tier0Api):
    def run_stream_completed(self, run_number):
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

    def test_get_run_class_names(self):
        workflow_run_classes = {'PromptCalibProdSiStripGains': ['Collisions15', 'Collisions16'],
                                'PromptCalibProdSiStrip': ['Collisions15', 'Collisions16'],
                                'PromptCalibProdSiPixelAli': ['Collisions15', 'Collisions16'],
                                'PromptCalibProdSiStripGainsAfterAbortGap': ['Collisions16'],
                                'PromptCalibProd': ['Collisions15', 'Collisions16']}

        expected_result = {'Collisions15', 'Collisions16'}
        run_class_names = discover.get_run_class_names(workflow_run_classes)
        self.assertEqual(run_class_names, expected_result)

        imaginary_workflow_run_classes = {'PromptCalibProdSiStripGains': ['Collisions15', 'A'],
                                          'PromptCalibProdSiStrip': ['ILOVE_CMS', 'Collisions16', 'B', 'C'],
                                          'RandomWorkflow': ['Collisions15', 'A'],
                                          'PromptCalibProd': ['E', 'Collisions16']}

        expected_result = {'Collisions15', 'Collisions16', 'A', 'B', 'C', 'E', 'ILOVE_CMS'}
        run_class_names = discover.get_run_class_names(imaginary_workflow_run_classes)
        self.assertEqual(run_class_names, expected_result)

    def test_update_runs(self):

        date = time.strftime("%d-%m-%Y_%H.%M.%S")
        engine = sqlalchemy.create_engine('sqlite:///test-{}.db'.format(date), echo=False)
        Base = declarative_base()
        Base.metadata.create_all(engine, checkfirst=True)
        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        session = Session()

        logger = LoggerMock('INFO')
        t0api_stream_completed = T0ApiStreamAlwaysCompleted()
        t0api_stream_not_completed = T0ApiStreamNeverCompleted()

        config = {"run_stream_timeout": 5}
        local_runs = []
        recent_runs = []

        discover.update_runs(logger, session, t0api_stream_completed, config, local_runs, recent_runs)

        # TODO: finish when RRApi server is working since real data is needed


if __name__ == '__main__':
    unittest.main()
