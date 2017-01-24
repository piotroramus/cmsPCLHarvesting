import unittest

from utils import other


class OtherTest(unittest.TestCase):
    def test_get_run_class_names(self):
        config = dict()
        config['workflows'] = dict()
        config['workflows']['PromptCalibProdSiStripGains'] = dict()
        config['workflows']['PromptCalibProdSiStripGains']['run_classes'] = ['Collisions15', 'Collisions16']
        config['workflows']['PromptCalibProdSiStrip'] = dict()
        config['workflows']['PromptCalibProdSiStrip']['run_classes'] = ['Collisions15', 'Collisions16']
        config['workflows']['PromptCalibProdSiPixelAli'] = dict()
        config['workflows']['PromptCalibProdSiPixelAli']['run_classes'] = ['Collisions15', 'Collisions16']
        config['workflows']['PromptCalibProdSiStripGainsAfterAbortGap'] = dict()
        config['workflows']['PromptCalibProdSiStripGainsAfterAbortGap']['run_classes'] = ['Collisions15',
                                                                                          'Collisions16']
        config['workflows']['PromptCalibProd'] = dict()
        config['workflows']['PromptCalibProd']['run_classes'] = ['Collisions15', 'Collisions16']

        expected_result = {'Collisions15', 'Collisions16'}
        run_class_names = other.get_run_class_names(config)
        self.assertEqual(run_class_names, expected_result)

        imaginary_config = dict()
        imaginary_config['workflows'] = dict()
        imaginary_config['workflows']['PromptCalibProdSiStripGains'] = dict()
        imaginary_config['workflows']['PromptCalibProdSiStripGains']['run_classes'] = ['Collisions15', 'A']
        imaginary_config['workflows']['PromptCalibProdSiStrip'] = dict()
        imaginary_config['workflows']['PromptCalibProdSiStrip']['run_classes'] = ['ILOVE_CMS', 'Collisions16', 'B', 'C']
        imaginary_config['workflows']['RandomWorkflow'] = dict()
        imaginary_config['workflows']['RandomWorkflow']['run_classes'] = ['Collisions15', 'A']
        imaginary_config['workflows']['PromptCalibProd'] = dict()
        imaginary_config['workflows']['PromptCalibProd']['run_classes'] = ['E', 'Collisions16']
        expected_result = {'Collisions15', 'Collisions16', 'A', 'B', 'C', 'E', 'ILOVE_CMS'}
        run_class_names = other.get_run_class_names(imaginary_config)
        self.assertEqual(run_class_names, expected_result)
