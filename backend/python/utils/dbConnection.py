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


def sqlite_connection_string(config):

    db_path = config['sqlite_db_path']
    connection_string = "sqlite:///{}".format(db_path)

    return connection_string


def get_connection_string(config):

    connections = {
        'oracle': oracle_connection_string,
        'sqlite': sqlite_connection_string
    }

    get_connection_method = connections[config['db_vendor']]
    return get_connection_method(config)
