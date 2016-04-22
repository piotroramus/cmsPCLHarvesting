from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# TODO #5: order this alphabetically by a name

class RunInfo(Base):
    __tablename__ = 'run_info'

    number = Column(Integer, primary_key=True)
    run_class_name = Column(String)
    bfield = Column(Float)
    start_time = Column(DateTime)
    stop_time = Column(DateTime)

    run_blocks = relationship("RunBlock")
    multirun = Column(Integer, ForeignKey('multirun.id'))

    def __repr__(self):
        return "RunInfo(number={}, run_class_name={}, bfield={} start_time={}, end_time={})".format(
            self.number, self.run_class_name, self.bfield, self.start_time, self.stop_time)


class RunBlock(Base):
    __tablename__ = 'run_block'

    id = Column(Integer, primary_key=True)
    block_name = Column(String)

    run_number = Column(Integer, ForeignKey('run_info.number'))


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

    run_numbers = relationship("RunInfo")
    filenames = relationship("Filename")
    # TODO #6: many-to-many relationship
    workflows = relationship("Workflow", back_populates="multirun")


class Filename(Base):
    __tablename__ = 'filename'

    id = Column(Integer, primary_key=True)
    filename = Column(String)

    multirun = Column(Integer, ForeignKey('multirun.id'))


class Workflow(Base):
    __tablename__ = 'workflow'

    id = Column(Integer, primary_key=True)
    workflow = Column(String)

    multirun_id = Column(Integer, ForeignKey('multirun.id'))
    multirun = relationship("Multirun", back_populates="workflows")
