import os
import sys
import unittest

sys.path.insert(0, os.path.abspath('..'))

from python import model


class ModelTest(unittest.TestCase):
    def test_dataset_repr(self):
        dataset_name_a = "/StreamExpress/Run2016D-PromptCalibProdSiStrip-Express-v2/ALCAPROMPT"
        dataset_name_b = "/A/B/C"

        dataset_a = model.Dataset()
        dataset_b = model.Dataset()

        dataset_a.dataset = dataset_name_a
        dataset_b.dataset = dataset_name_b

        dataset_repr_a = str(dataset_a)
        dataset_repr_b = str(dataset_b)

        self.assertEqual(dataset_repr_a, dataset_name_a)
        self.assertEqual(dataset_repr_b, dataset_name_b)

    def test_filename_repr(self):
        name = '/store/express/Run2016D/StreamExpress/ALCAPROMPT/PromptCalibProdSiStrip-Express-v2/000/276/502/00000/AE18EB7B-FA44-E611-8C8B-02163E011CB1.root'
        filename = model.Filename()
        filename.filename = name
        filename_repr = str(filename)
        self.assertEqual(filename_repr, name)

    def test_multirun_repr(self):
        id = 32
        number_of_events = 100000
        bfield = 3.8033490534589345
        run_class_name = 'Cosmics'
        cmssw = "CMSSW_8_0_11"
        scram_arch = 'slc6_amd64_gcc530'
        scenario = 'ppEra_Run2_2016'
        global_tag = '80X_dataRun2_Express_v10'
        failure_retries = 0
        no_payload_retries = 0
        run_numbers = []
        dataset = '/A/B/C'
        state = 'processed_ok'

        multirun = model.Multirun()
        multirun.id = id
        multirun.number_of_events = number_of_events
        multirun.bfield = bfield
        multirun.run_class_name = run_class_name
        multirun.cmssw = cmssw
        multirun.scram_arch = scram_arch
        multirun.scenario = scenario
        multirun.global_tag = global_tag
        multirun.no_payload_retries = no_payload_retries
        multirun.failure_retries = failure_retries
        multirun.run_numbers = run_numbers
        multirun.dataset = dataset
        multirun.state = state

        multirun_repr = str(multirun)
        multirun_expected = ("Multirun(id={}, "
                             "number_of_events={}, "
                             "dataset={}, "
                             "bfield={}, "
                             "run_class_name={}, "
                             "cmssw={}, "
                             "scram_arch={}, "
                             "scenario={}, "
                             "global_tag={}, "
                             "retries={}, "
                             "state={}, "
                             "run_numbers={})").format(id, number_of_events, dataset, bfield, run_class_name, cmssw,
                                                       scram_arch, scenario, global_tag, no_payload_retries, state, run_numbers)

        self.assertEqual(multirun_repr, multirun_expected)

    def test_mutlirunstate_repr(self):
        state_1 = 'need_more_data'
        state_2 = 'processed_ok'

        multirun_state = model.MultirunState()

        multirun_state.state = state_1
        self.assertEqual(str(multirun_state), state_1)

        multirun_state.state = state_2
        self.assertEqual(str(multirun_state), state_2)

    def test_runinfo_repr(self):
        number = 234567
        run_class_name = 'Collisions16'
        bfield = 3.865756
        start_time = '2016-07-09 08:33:52.000000'
        stream_completed = True
        stream_timeout = False
        used = False
        used_datasets = []

        run_info = model.RunInfo()
        run_info.number = number
        run_info.run_class_name = run_class_name
        run_info.bfield = bfield
        run_info.start_time = start_time
        run_info.stream_completed = stream_completed
        run_info.stream_timeout = stream_timeout
        run_info.used = used

        run_info_repr = str(run_info)
        run_info_expected = ("RunInfo(number={}, "
                             "run_class_name={}, "
                             "bfield={}, "
                             "start_time={}, "
                             "stream_completed={}, "
                             "used={}, "
                             "used_datasets={}").format(number, run_class_name, bfield, start_time, stream_completed,
                                                        used, used_datasets)

        self.assertEqual(run_info_expected, run_info_repr)


if __name__ == '__main__':
    unittest.main()
