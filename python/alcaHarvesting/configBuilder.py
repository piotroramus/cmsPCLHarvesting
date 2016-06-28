import logging

import logs.logger as logs
import Configuration.DataProcessing.GetScenario as cmssw
import FWCore.ParameterSet.Config as cms


class AlCaHarvestingCfgBuilder(object):
    def __init__(self):
        logs.setup_logging()
        self.logger = logging.getLogger(__name__)

    def build(self, dataset, alcapromptdataset, input_files, scenario, global_tag, output_file, workflows=None):

        if not output_file.endswith(".py"):
            output_file += ".py"

        try:
            scenario = cmssw.getScenario(scenario)
        except Exception as ex:
            msg = "Error getting Scenario implementation for {}\n{}".format(scenario, ex)
            raise RuntimeError(msg)

        self.logger.info("Retrieved Scenario: {}".format(scenario))
        self.logger.info("Using Global Tag: {}".format(global_tag))
        self.logger.info("Dataset: {}".format(dataset))

        try:
            kwds = dict()
            if workflows:
                kwds['skims'] = workflows
            if alcapromptdataset:
                kwds['alcapromptdataset'] = alcapromptdataset
            process = scenario.alcaHarvesting(global_tag, dataset, **kwds)
        except Exception as ex:
            msg = "Error creating AlcaHarvesting config:\n{}".format(ex)
            raise RuntimeError(msg)

        for input_file in input_files:
            process.source.fileNames.append(input_file)

        # fix in order to make multiruns work
        process.DQMStore.collateHistograms = cms.untracked.bool(True)
        process.dqmSaver.forceRunNumber = cms.untracked.int32(999999)

        with open(output_file, "w") as alcacfg:
            alcacfg.write(process.dumpPython())

        cms_run = "cmsRun -j FrameworkJobReport.xml {}".format(output_file)
        self.logger.info("Now do:\n{}".format(cms_run))
