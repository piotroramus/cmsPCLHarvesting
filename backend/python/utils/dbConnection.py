import json
import re


def oracle_connection_string(config):
    with open(config['tns_file']) as tns_file:
        tns = tns_file.read()

    tns = re.sub(r'[\s\n]+', '', tns)

    with open(config['oracle_secret']) as secret_file:
        secret = json.load(secret_file)

    connection_string = "oracle+cx_oracle://{}:{}@{}".format(secret['username'], secret['password'], tns)

    return connection_string
