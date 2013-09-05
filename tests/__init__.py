#!/usr/bin/python
# coding: utf-8
'''
Module defines setUp and tearDown actions of
package lever for tests.

Functionality is not complete.
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.utils.db_fixture import (
    Base, Flavors, Images,
    MacAddressPool, Instance,
    dump_data
)

connection_string = 'mysql+mysqldb://testing:testing@localhost/testing?charset=utf8'
engine = create_engine(connection_string)

Session = sessionmaker(bind=engine)


def setUpPackage():
    Base.metadata.create_all(engine)
    s = Session()

    dump_data()


def tearDownPackage():
    if any([engine.has_table(key) for key in Base.metadata.tables.keys()]):
        Base.metadata.drop_all(engine)
