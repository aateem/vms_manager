#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Provides data mapping of entities from
database to python classes. Schema is
autoloaded.(Different approach of this functionality
may be done considering using defined classes
from src.utils.db_fixture module as soon
as they declare schema explicitly)

Also provides toolkit to using session objects
inside of with context manager.
'''

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Table

#following exceptions is using in tests
from sqlalchemy.orm.exc import (
    NoResultFound, MultipleResultsFound
)

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
