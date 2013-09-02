#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

connection_string = 'mysql+mysqldb://devel:devel@localhost/devel?charset=utf8'
engine = create_engine(connection_string, echo=True)

Base = declarative_base()
Session = sessionmaker(bind=engine)


class Entity(Base):
    __tablename__ = 'entity'

    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    another_entity_id = relationship("AnotherEntity",
                                    backref='entity')

    def __init__(self, name):
        self.name = name


class AnotherEntity(Base):
    __tablename__ = 'another_entity'

    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    entity_id = Column(Integer, ForeignKey('entity.id'))

    def __init__(self, name):
        self.name = name
