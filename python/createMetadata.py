import argparse
import logging
import xml.etree.ElementTree as ET
import json

import logs.logger as logs

if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("job_report", help="location of xml file containing encoded metadata")
    parser.add_argument("output_file", help="name of output file")
    parser.add_argument("multirun_dir_id", help="directory multi-run is stored")
    args = parser.parse_args()

    xml_file = args.job_report
    output_file = args.output_file
    multirun_dir_id = args.multirun_dir_id
    tree = ET.parse(xml_file)

    prep_meta_data = tree.findall("./AnalysisFile/prepMetaData[@Value]")
    elem = prep_meta_data[0].attrib['Value']

    as_json = json.loads(str(elem))
    as_json['userText'] = "PCL MultiRun Upload for SiStrip Gains calib. (prep). MultiRun directory ID: {}".format(multirun_dir_id)
    metadata = json.dumps(as_json, indent=4, sort_keys=True)

    with open(output_file, 'w') as f:
        f.write(metadata)
