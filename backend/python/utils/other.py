import re


def extract_dataset_parts(dataset):
    pattern = r'/(?P<primary_dataset>.*)/(?P<processed_dataset>.*?)/ALCAPROMPT'
    ds = re.match(pattern, dataset)
    return ds.group('primary_dataset'), ds.group('processed_dataset')


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

    return result


def get_run_class_names(config):
    run_class_names = set()
    for workflow_list in config['workflows'].itervalues():
        for rcn in workflow_list['run_classes']:
            run_class_names.add(rcn)
    return run_class_names


def to_be_uploaded(dataset, config):
    dataset_workflow = extract_workflow(dataset)
    for workflow in config['workflows']:
        if workflow == dataset_workflow:
            return config['workflows'][workflow]['payload_upload']
    return False
