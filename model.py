from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Table

Base = declarative_base()


# TODO #5: order this alphabetically by a name


run_multirun_assoc = Table('run_multirun', Base.metadata,
                           Column('multirun_id', Integer, ForeignKey('multirun.id')),
                           Column('run_info_id', Integer, ForeignKey('run_info.number')))


class RunInfo(Base):
    __tablename__ = 'run_info'

    number = Column(Integer, primary_key=True)
    run_class_name = Column(String)
    bfield = Column(Float)
    start_time = Column(DateTime)
    stop_time = Column(DateTime)

    run_blocks = relationship("RunBlock")
    multiruns = relationship("Multirun", secondary=run_multirun_assoc, back_populates="run_numbers")

    def __repr__(self):
        return "RunInfo(number={}, run_class_name={}, bfield={} start_time={}, end_time={})".format(
            self.number, self.run_class_name, self.bfield, self.start_time, self.stop_time)


class RunBlock(Base):
    __tablename__ = 'run_block'

    id = Column(Integer, primary_key=True)
    block_name = Column(String)

    run_number = Column(Integer, ForeignKey('run_info.number'))

    def __repr__(self):
        return "RunBlock(id={}, block_name={}, run_number={}".format(self.id, self.block_name, self.run_number)


class Multirun(Base):
    __tablename__ = 'multirun'

    id = Column(Integer, primary_key=True)
    number_of_events = Column(Integer)
    dataset = Column(String)
    bfield = Column(Float)
    run_class_name = Column(String)
    cmssw = Column(String)
    scram_arch = Column(String)
    scenario = Column(String)
    global_tag = Column(String)
    closed = Column(Boolean)

    run_numbers = relationship("RunInfo", secondary=run_multirun_assoc, back_populates="multiruns")
    filenames = relationship("Filename")
    # TODO #6: many-to-many relationship
    workflows = relationship("Workflow", back_populates="multirun")

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
                "closed={}, "
                "run_numbers={}, "
                "filenames={}, "
                "workflows={}").format(self.id, self.number_of_events, self.dataset, self.bfield, self.run_class_name,
                                       self.cmssw, self.scram_arch, self.scenario, self.global_tag, self.closed,
                                       self.run_numbers, self.filenames, self.workflows)


class Filename(Base):
    __tablename__ = 'filename'

    id = Column(Integer, primary_key=True)
    filename = Column(String)

    multirun = Column(Integer, ForeignKey('multirun.id'))

    def __repr__(self):
        return self.filename


class Workflow(Base):
    __tablename__ = 'workflow'

    id = Column(Integer, primary_key=True)
    workflow = Column(String)

    multirun_id = Column(Integer, ForeignKey('multirun.id'))
    multirun = relationship("Multirun", back_populates="workflows")

    def __repr__(self):
        return self.workflow
