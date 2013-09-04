#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Main purpose of this module is initiation of all necessary data storages
(slq database and key-value storage) and filling it with all needed
data.

Also another main function of this module is wiping out data from
previous launches of system. This means dropping tables from
sql database and drop whole database which contains images from
key-value storage.

Main convinience of this module is that it can provide initial data set
not only for production database but also fixture data for test database
since initial state of mentioned is same as that in prodaction db.

This process (processing production db or test db data) is controlled by
argument for dump_data function. This arg has default value set to devel
deployment argument for production depoyment. If this code is using for
depoying test database function dump_data is called with deployment_arg
set to testing.
'''

import sys
import os.path

import gridfs
import pymongo

from sqlalchemy import (
    create_engine, Column, Integer,
    String, ForeignKey, Boolean
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class Flavors(Base):
    __tablename__ = 'flavors'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    vcpu = Column(Integer)
    memory = Column(Integer)


class Images(Base):
    __tablename__ = 'images'

    id = Column(String(50), primary_key=True, autoincrement=False)
    name = Column(String(50))
    fmt = Column(String(20))
    size = Column(Integer)


class MacAddressPool(Base):
    __tablename__ = 'mac_address_pool'

    id = Column(Integer, primary_key=True)
    address = Column(String(50))
    is_free = Column(Boolean)


class Instance(Base):
    __tablename__ = 'instance'

    id = Column(String(50), primary_key=True, autoincrement=False)
    domain_name = Column(String(50))
    state = Column(String(50))

    mac_addr = Column(Integer, ForeignKey('mac_address_pool.id'))


def dump_data(deployment_arg='devel'):
    #create proper accredetation for database
    connection_string = 'mysql+mysqldb://{0}:{0}@localhost/{0}?charset=utf8'.format(deployment_arg)
    engine = create_engine(connection_string)

    #get instance of Database object via proxy mongo client object
    #(which is listening on localhost
    #and 27017 port). This db object will be passed to GridFS instance which
    #provides toolkit for uploading files to mongoDB.
    #If debug_arg is equal to 'devel' perforimg cleaning
    #(simply dropping data base which contains images)
    #if there exists any data. Only after that one can upload image to gridfs.
    with pymongo.MongoClient() as client:
        #test presence of databases
        if deployment_arg == 'devel':
            if deployment_arg in client.database_names():
                client.drop_database(deployment_arg)

        db = client[deployment_arg]
        grfs = gridfs.GridFS(db)

        # path to image which will be uploaded to mongo storage.
        path_to_image = os.path.join(
            os.path.split(
                os.path.split(
                    os.path.split(os.path.abspath(__file__))[0]
                )[0]
            )[0],
            'data/pattern_for_lv_wrapper.img'
        )

        with open(path_to_image) as f:
            image_id = grfs.put(f, name="pattern_for_lv_wrapper.img")

    #processing sql data: if script is executing in production deployment
    #cleaning existing (if any) data
    #from previous launches of system and then creating new
    #schema with filling it with needed values.

    #TODO: make test of schema existing more sophisticated
    if deployment_arg == 'devel':
        if any([engine.has_table(key) for key in Base.metadata.tables.keys()]):
            Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)

    flavors = []
    flavors.append(Flavors(name="standart", vcpu=1, memory=524288))
    flavors.append(Flavors(name="memory_extend", vcpu=1, memory=1000000))
    flavors.append(Flavors(name="cpu_extend", vcpu=2, memory=524288))
    flavors.append(Flavors(name="vip", vcpu=2, memory=1000000))

    images = []
    images.append(
        Images(
            id=str(image_id),
            name='ubuntu12.04server',
            fmt='qcow2',
            size=1400
        )
    )

    mac_addresses = []
    mac_addresses.append(MacAddressPool(address="52:54:00:83:df:a1", is_free=True))
    mac_addresses.append(MacAddressPool(address="52:54:00:83:df:a2", is_free=True))
    mac_addresses.append(MacAddressPool(address="52:54:00:83:df:a3", is_free=True))
    mac_addresses.append(MacAddressPool(address="52:54:00:83:df:a4", is_free=True))

    # Put objects into session and flush to database
    Session = sessionmaker(bind=engine)
    s = Session()

    s.add_all(flavors)
    s.add_all(mac_addresses)
    s.add_all(images)

    s.flush()
    s.commit()
    s.close()

    #engine must be returne
