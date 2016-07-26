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
    args = parser.parse_args()

    xml_file = args.job_report
    output_file = args.output_file

    tree = ET.parse(xml_file)

    prep_meta_data = tree.findall("./AnalysisFile/prepMetaData[@Value]")
    elem = prep_meta_data[0].attrib['Value']

    as_json = json.loads(str(elem))
    metadata = json.dumps(as_json, indent=4, sort_keys=True)

    with open(output_file, 'w') as f:
        f.write(metadata)
