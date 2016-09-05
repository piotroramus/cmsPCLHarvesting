import argparse
import logging
import sqlalchemy

import model
import logs.logger as logs
import utils.configReader as configReader
import utils.dbConnection as dbConnection

if __name__ == '__main__':
    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("multirun_id", type=int, help="id of processed multi-run")
    parser.add_argument("multirun_eos_dir", help="directory in the eos multi-run was uploaded to")
    parser.add_argument("config_file", help="path to configuration file")
    args = parser.parse_args()

    multirun_id = args.multirun_id
    eos_dir = args.multirun_eos_dir
    config_file = args.config_file

    config = configReader.read(config_file)

    connection_string = dbConnection.oracle_connection_string(config)
    engine = sqlalchemy.create_engine(connection_string, echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    eos_dir_obj = model.EosDir()
    eos_dir_obj.eos_dir = eos_dir
    eos_dir_obj.multirun_id = multirun_id
    session.add(eos_dir_obj)

    session.commit()
