import re


def extract_workflow(dataset):
    pattern = r'/(?P<primary_dataset>.*)/(?P<acquisition_era>.*?)-(?P<workflow>.*?)-(?P<version>.*)/ALCAPROMPT'
    workflow = re.match(pattern, dataset)
    if not workflow:
        raise ValueError("Couldn't determine workflow out of dataset name {}".format(dataset))
    # TODO #9: check if workflow is correct in autoPCL
    return workflow.group('workflow')
