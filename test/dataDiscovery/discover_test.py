import os
import sys
import unittest

sys.path.insert(0, os.path.abspath('../../python'))

from dataDiscovery import discover


class DiscoverTest(unittest.TestCase):
    def test_discover(self):
        pass

    def test_get_base_release(self):
        valid_releases = [
            'CMSSW_8_0_10',
            "CMSSW_9_1_1",
            "CMSSW_10_0_11"
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


if __name__ == '__main__':
    unittest.main()
