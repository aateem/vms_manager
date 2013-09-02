#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.schema import Table

conn_string = 'mysql+mysqldb://devel:devel@localhost/devel?charset=utf8'
engine = create_engine(conn_string, echo=False)

Base = declarative_base()
Session = sessionmaker(bind=engine)


class Entity(Base):
    __table__ = Table('entity',
                      Base.metadata,
                      autoload=True,
                      autoload_with=engine)

    another_entity = relationship('AnotherEntity', backref='another_entities')


class AnotherEntity(Base):
    __table__ = Table('another_entity',
                      Base.metadata,
                      autoload=True,
                      autoload_with=engine)
