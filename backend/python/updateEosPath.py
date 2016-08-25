import argparse
import logging
import sqlalchemy

import model
import logs.logger as logs

if __name__ == '__main__':

    logs.setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("multirun_id", type=int, help="id of processed multi-run")
    parser.add_argument("db_path", help="location of database containing multi-run info")
    parser.add_argument("multirun_eos_dir", help="directory in the eos multi-run was uploaded to")
    args = parser.parse_args()

    multirun_id = args.multirun_id
    db_path = args.db_path
    eos_dir = args.multirun_eos_dir

    engine = sqlalchemy.create_engine('sqlite:///{}'.format(db_path), echo=False)
    model.Base.metadata.create_all(engine, checkfirst=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    eos_dir_obj = model.EosDir()
    eos_dir_obj.eos_dir = eos_dir
    eos_dir_obj.multirun_id = multirun_id
    session.add(eos_dir_obj)

    session.commit()
