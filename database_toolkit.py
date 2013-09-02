#!/usr/bin/python
# -*- coding: utf-8 -*-

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Table

import pymongo
import gridfs
from bson.objectid import ObjectId

connection_string = 'mysql+mysqldb://devel:devel@localhost/devel?charset=utf8'
engine = create_engine(connection_string)

Base = declarative_base()
Session = sessionmaker(bind=engine)  # sessions fabric


class Flavor(Base):
    __table__ = Table('flavors',
                      Base.metadata,
                      autoload=True,
                      autoload_with=engine)


class Image(Base):
    __table__ = Table('images',
                      Base.metadata,
                      autoload=True,
                      autoload_with=engine)


class MacAddress(Base):
    __table__ = Table('mac_address_pool',
                      Base.metadata,
                      autoload=True,
                      autoload_with=engine)


class Instance(Base):
    __table__ = Table('instance',
                      Base.metadata,
                      autoload=True,
                      autoload_with=engine)


@contextmanager
def contexted_session():
    '''
    This recipe is taken from sqlalchemy documentation.

    Code of this function provides session handling
    that can be used inside of with context manager.
    '''
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
