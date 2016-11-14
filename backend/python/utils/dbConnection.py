import json
import os
import requests


def resolve_tns():
    tnsnames_url = "http://service-oracle-tnsnames.web.cern.ch/service-oracle-tnsnames/tnsnames.ora"

    tns = requests.get(tnsnames_url)
    with open('tnsnames.ora', 'w') as tns_file:
        tns_file.write(tns.content)

    os.environ["TNS_ADMIN"] = os.getcwd()


def oracle_connection_string(config):
    resolve_tns()

    with open(config['oracle_secret']) as secret_file:
        secret = json.load(secret_file)

    connection_string = "oracle+cx_oracle://{}:{}@{}".format(secret['username'], secret['password'],
                                                             secret['database'])
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
