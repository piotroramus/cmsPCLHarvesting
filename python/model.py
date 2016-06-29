from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
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


run_block_assoc = Table('run_block', Base.metadata,
                        Column('run_id', Integer, ForeignKey('run_info.number')),
                        Column('block_id', Integer, ForeignKey('block.id')))


class Block(Base):
    __tablename__ = 'block'

    id = Column(Integer, primary_key=True)
    block_name = Column(String)

    def __repr__(self):
        return self.block_name


class Dataset(Base):
    __tablename__ = 'dataset'

    id = Column(Integer, primary_key=True)
    dataset = Column(String)

    def __repr__(self):
        return self.dataset


class Filename(Base):
    __tablename__ = 'filename'

    id = Column(Integer, primary_key=True)
    filename = Column(String)

    multirun = Column(Integer, ForeignKey('multirun.id'))

    def __repr__(self):
        return self.filename


class Multirun(Base):
    __tablename__ = 'multirun'

    id = Column(Integer, primary_key=True)
    number_of_events = Column(Integer)
    bfield = Column(Float)
    run_class_name = Column(String)
    cmssw = Column(String)
    scram_arch = Column(String)
    scenario = Column(String)
    global_tag = Column(String)
    retries = Column(Integer)
    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    state_id = Column(Integer, ForeignKey('multirun_state.id'))

    dataset = relationship("Dataset")
    state = relationship("MultirunState")
    run_numbers = relationship("RunInfo", secondary=run_multirun_assoc)
    filenames = relationship("Filename")

    def __repr__(self):
        return ("Multirun(id={}, "
                "number_of_events={}, "
                "dataset={}, "
                "bfield={}, "
                "run_class_name={}, "
                "cmssw={}, "
                "scram_arch={}, "
                "scenario={}, "
                "global_tag={}, "
                "retries={}, "
                "state={}, "
                "run_numbers={}, "
                "filenames={})").format(self.id, self.number_of_events, self.dataset, self.bfield, self.run_class_name,
                                        self.cmssw, self.scram_arch, self.scenario, self.global_tag, self.retries,
                                        self.state, self.run_numbers, self.filenames)


class MultirunState(Base):
    __tablename__ = 'multirun_state'

    id = Column(Integer, primary_key=True)
    state = Column(String, unique=True)

    def __repr__(self):
        return self.state


class RunInfo(Base):
    __tablename__ = 'run_info'

    number = Column(Integer, primary_key=True)
    run_class_name = Column(String)
    bfield = Column(Float)
    start_time = Column(DateTime)
    stream_completed = Column(Boolean)
    used = Column(Boolean)

    used_datasets = relationship("Dataset", secondary=run_dataset_assoc)
    blocks = relationship("Block", secondary=run_block_assoc)

    def __repr__(self):
        return ("RunInfo(number={}, "
                "run_class_name={}, "
                "bfield={}, "
                "start_time={}, "
                "stream_completed={}, "
                "used={}, "
                "used_datasets={}, "
                "blocks={}, ").format(self.number, self.run_class_name, self.bfield, self.start_time,
                                      self.stream_completed, self.used, self.used_datasets, self.blocks)
