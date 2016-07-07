import re


def extract_workflow(dataset, available_workflows=None):
    pattern = r'/(?P<primary_dataset>.*)/(?P<acquisition_era>.*?)-(?P<workflow>.*?)-(?P<version>.*)/ALCAPROMPT'
    workflow = re.match(pattern, dataset)
    if not workflow:
        raise ValueError("Couldn't determine workflow out of dataset name {}".format(dataset))
    result = workflow.group('workflow')

    # we want to check it only when there is a new dataset (available_workflows parameter should be passed then)
    if available_workflows and result not in available_workflows:
        raise ValueError(
            "Dataset {} contains unknown workflow {}. Check config for possible workflow set!".format(dataset, result))

    return workflow.group('workflow')
