#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path

import xml.etree.ElementTree as ElementTree
import libvirt
import pymongo
import gridfs
from bson.objectid import ObjectId

from src.database_toolkit import Flavor, Image, MacAddress, Instance, contexted_session

# in future these next flobals may be moved to config file
PROJECTS_PATH = '/home/aroma/Programming/sandbox/test/data/'
XML_PATTERN_FOR_INSTANCE = '/home/aroma/Programming/sandbox/test/data/domain_pattern.xml'


class NovaMimic:
    #TODO: make function to take named arguments
    def instance_boot(self, instance_name, image_id, flavor_id):
        '''
        Function boots instance with given name, image id and flavor id.

        Image id is used to fetch informtion about image which will be using for
        booting up VM instance. Image information include: metadata on image (name, format, size)
        and key for retrieving image itself from key-value storage.

        Flavor id is used to fetch information about virtual hardware (amount of RAM and virtual CPU)
        that will be provisioned to VM instance by building xml configuration file for libvirt.

        Returns: information about booted instance
            - name
            - id (md5 from date of boot)
        '''
        # create directory for instance project (include xml file for libvirt
        # and image for booting)
        self.current_project_path = os.path.join(PROJECTS_PATH, instance_name)
        if not os.path.exists(self.current_project_path):
            os.mkdir(self.current_project_path)

        # get flavor data from database
        with contexted_session() as s:
            flavor = s.query(Flavor).filter(Flavor.id == flavor_id).one()
            image = s.query(Image).filter(Image.id == image_id).one()
            # first free mac address
            mac_address = s.query(MacAddress).filter(MacAddress.is_free == True).first()

            self._xml_processing(instance_name, image.name, flavor.memory, flavor.vcpu, mac_address.address)
            self._image_processing(image.name, image.storage_key)


    def _xml_processing(self, instance_name, image_name, memory, vcpu, mac_address):
        # parse pattern xml config and update needed sections in order to make
        # own config
        instance_config = ElementTree.parse(XML_PATTERN_FOR_INSTANCE)
        doc_root = instance_config.getroot()

        # updating name of instance
        name = doc_root.find('name')
        name.text = instance_name

        # amount of memory that will be available to instance
        doc_root.find('memory').text = str(memory)

        # amount of currentMemory is equal to total memory for this
        # instance
        doc_root.find('currentMemory').text = str(memory)

        # vcpu
        doc_root.find('vcpu').text = str(vcpu)

        # path to image which will be used for booting
        devices = doc_root.find('devices')

        for disk in devices.findall('disk'):
            if disk.get('type') == 'file':
                disk.find('source').set(
                    'file',
                    os.path.join(
                        self.current_project_path,
                        '{0}.img'.format(image_name)
                    )
                )

        # mac address for this instance
        for interface in devices.findall('interface'):
            if interface.get('type') == 'network':
                interface.find('mac').set('address', mac_address)

        # write config
        instance_config.write(
            os.path.join(
                self.current_project_path,
                '{0}.xml'.format(instance_name)
            )
        )

    def _image_processing(self, image_name, storage_key):
        # get connection with mongoDB via creating client and download image
        # using gridfs module
        with pymongo.MongoClient() as client:
            storage = client.image_storage
            grfs = gridfs.GridFS(storage)

            with open(os.path.join(self.current_project_path, '{0}.img'.format(image_name)), 'wb') as f:
                grout = grfs.get(ObjectId(storage_key))
                f.write(grout.read())

    def instance_reboot(self, instance_id):
        pass

    def instance_shutdown(self, instance_id):
        pass

    def instance_destroy(self, instance_id):
        pass

    def image_list(self):
        pass

    def flavor_list(self):
        pass
