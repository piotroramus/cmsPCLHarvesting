from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Table

Base = declarative_base()

run_multirun_assoc = Table('run_multirun', Base.metadata,
                           Column('multirun_id', Integer, ForeignKey('multirun.id')),
                           Column('run_info_id', Integer, ForeignKey('run_info.number')))

run_dataset_assoc = Table('run_dataset', Base.metadata,
                          Column('run_id', Integer, ForeignKey('run_info.number')),
                          Column('dataset_id', Integer, ForeignKey('dataset.id')))


class Dataset(Base):
    __tablename__ = 'dataset'

    id = Column(Integer, Sequence('id'), primary_key=True)
    dataset = Column(String(128), unique=True)

    def __repr__(self):
        return self.dataset


class EosDir(Base):
    __tablename__ = 'eos_dir'

    id = Column(Integer, Sequence('id'), primary_key=True)
    eos_dir = Column(String(128), unique=True)

    multirun_id = Column(Integer, ForeignKey('multirun.id'))

    def __repr__(self):
        return self.eos_dir


class Filename(Base):
    __tablename__ = 'filename'

    id = Column(Integer, Sequence('id'), primary_key=True)
    filename = Column(String(256), unique=True)

    multirun = Column(Integer, ForeignKey('multirun.id'))

    def __repr__(self):
        return self.filename


class Multirun(Base):
    __tablename__ = 'multirun'

    id = Column(Integer, Sequence('id'), primary_key=True)
    creation_time = Column(DateTime, nullable=False)
    number_of_events = Column(Integer)
    bfield = Column(Float)
    run_class_name = Column(String(64))
    cmssw = Column(String(32))
    scram_arch = Column(String(32))
    scenario = Column(String(64))
    global_tag = Column(String(128))
    perform_payload_upload = Column(Boolean, nullable=False)
    no_payload_retries = Column(Integer, nullable=False)
    failure_retries = Column(Integer, nullable=False)
    dropbox_log = Column(String(256))
    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    state_id = Column(Integer, ForeignKey('multirun_state.id'), nullable=False)

    dataset = relationship("Dataset")
    eos_dirs = relationship("EosDir")
    filenames = relationship("Filename")
    processing_times = relationship("ProcessingTime")
    run_numbers = relationship("RunInfo", secondary=run_multirun_assoc)
    state = relationship("MultirunState")

    def to_json(self):
        return {
            'id': self.id,
            'creation_time': self.creation_time.isoformat(),
            'number_of_events': self.number_of_events,
            'bfield': self.bfield,
            'run_class_name': self.run_class_name,
            'cmssw': self.cmssw,
            'scram_arch': self.scram_arch,
            'scenario': self.scenario,
            'global_tag': self.global_tag,
            'perform_payload_upload': self.perform_payload_upload,
            'no_payload_retries': self.no_payload_retries,
            'failure_retries': self.failure_retries,
            'dropbox_log': self.dropbox_log,
            'dataset': self.dataset.dataset,
            'eos_dirs': self.__eos_dirs_json(),
            'processing_times': self.__processing_times_json(),
            'runs': self.__runs__json(),
            'state': self.state.state,
        }

    def __eos_dirs_json(self):
        return [ed.eos_dir for ed in self.eos_dirs]

    def __processing_times_json(self):
        times = list()
        for t in self.processing_times:
            single_entry = list()
            # TODO: isoformat
            single_entry.append(t.start_time)
            single_entry.append(t.end_time)
            times.append(single_entry)
        return times

    def __runs__json(self):
        return [r.to_json() for r in self.run_numbers]

    def __repr__(self):
        return ("Multirun(id={}, "
                "creation_time={}, "
                "number_of_events={}, "
                "dataset={}, "
                "bfield={}, "
                "run_class_name={}, "
                "cmssw={}, "
                "scram_arch={}, "
                "scenario={}, "
                "perform_payload_upload={}, "
                "global_tag={}, "
                "no_payload_retries={}, "
                "failure_retries={}, "
                "state={}, "
                "run_numbers={})").format(self.id, self.creation_time, self.number_of_events, self.dataset, self.bfield,
                                          self.run_class_name, self.cmssw, self.scram_arch, self.scenario,
                                          self.global_tag, self.perform_payload_upload, self.no_payload_retries,
                                          self.failure_retries, self.state, self.run_numbers)


class MultirunState(Base):
    __tablename__ = 'multirun_state'

    id = Column(Integer, Sequence('id'), primary_key=True)
    state = Column(String(32), unique=True)

    def __repr__(self):
        return self.state


class ProcessingTime(Base):
    __tablename__ = 'processing_time'

    id = Column(Integer, Sequence('id'), primary_key=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    multirun_id = Column(Integer, ForeignKey('multirun.id'))

    def __repr__(self):
        return "[{} - {}]".format(self.start_time, self.end_time)


class RunInfo(Base):
    __tablename__ = 'run_info'

    number = Column(Integer, primary_key=True)
    run_class_name = Column(String(32))
    bfield = Column(Float)
    start_time = Column(DateTime)
    stream_completed = Column(Boolean, nullable=False)
    stream_timeout = Column(Boolean, nullable=False)
    used = Column(Boolean)

    used_datasets = relationship("Dataset", secondary=run_dataset_assoc)

    def to_json(self):
        return {
            'number': self.number,
        }

    def __repr__(self):
        return ("RunInfo(number={}, "
                "run_class_name={}, "
                "bfield={}, "
                "start_time={}, "
                "stream_completed={}, "
                "used={}, "
                "used_datasets={})").format(self.number, self.run_class_name, self.bfield, self.start_time,
                                            self.stream_completed, self.used, self.used_datasets)
