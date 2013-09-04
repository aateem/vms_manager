#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import shutil
import unittest
import xml.etree.ElementTree as ElementTree

from mock import patch, Mock
import libvirt

import src.nova_mimic
from src.database_toolkit import (
    Flavor, Image, MacAddress, Instance,
    contexted_session, NoResultFound,
    MultipleResultsFound
)

#directory where images will be stored
PATH_TO_TEST_PROJECTS_DIR = os.path.abspath(os.path.dirname(__file__))
#path to config which store global setting for system
PATH_TO_GLOBAL_CONFIG = os.path.join(
    os.path.split(
        PATH_TO_TEST_PROJECTS_DIR
    )[0],
    'config.ini'
)


#just for remembering exception handling
class MyException(Exception):
    pass


class TestNovaMimicBootMethod(unittest.TestCase):
    def setUp(self):
        self.path_to_image_storage = os.path.join(
            PATH_TO_TEST_PROJECTS_DIR,
            'image_storage'
        )
        os.mkdir(self.path_to_image_storage)

        self.libvirt_conn = libvirt.open("qemu:///system")

        with patch(
            'src.nova_mimic.PATH_TO_GLOBAL_CONFIG',
            PATH_TO_GLOBAL_CONFIG
        ):
            self.nova_mimic_instance = src.nova_mimic.NovaMimic()

    def tearDown(self):
        '''
        Destroys all domains which were
        started.

        Closes connectin to libvirt driver.

        Removes test image storage directory
        with all contents (i.e. image files)
        '''

        for domain in self.nova_mimic_instance.domains_pool.values():
            domain.destroy()

        self.libvirt_conn.close()

        #remove test image storage directory with all content
        if os.path.exists(self.path_to_image_storage):
            shutil.rmtree(self.path_to_image_storage)

    def test_xml_processing(self):
        '''
        Checks if string that is produced
        by _xml_processing method is correct
        (i.e. needed attributes have proper values)
        '''
        fixture_data = {
            'args':
            {
                'instance_name': 'test_instance',
                'image_id': '522700a8a063d875c192d818',
                'memory': 524288,
                'vcpu': 1,
                'mac_address': '52:54:00:83:df:a1'
            },
            'flavor_id': 1
        }

        with patch.object(
            self.nova_mimic_instance,
            'path_to_image_storage',
            self.path_to_image_storage
        ):
            xml_conf_string = self.nova_mimic_instance._xml_processing(
                **fixture_data['args']
            )

        # query data from db to compare against corresponding values in config
        with contexted_session() as s:
            flavor = s.query(Flavor)\
                      .filter(Flavor.id == fixture_data['flavor_id'])\
                      .one()

            image = s.query(Image)\
                     .filter(Image.id == fixture_data['args']['image_id'])\
                     .one()

            # parse xml config from string
            conf_root = ElementTree.fromstring(xml_conf_string)

            # check consistency
            name = conf_root.find("name")
            self.assertEqual(name.text, fixture_data['args']['instance_name'])

            memory = conf_root.find("memory")
            self.assertEqual(int(memory.text), flavor.memory)

            current_memory = conf_root.find("currentMemory")
            self.assertEqual(int(current_memory.text), flavor.memory)

            vcpu = conf_root.find("vcpu")
            self.assertEqual(int(vcpu.text), flavor.vcpu)

            devices = conf_root.find("devices")
            for disk in devices.findall("disk"):
                if disk.get("type") == "file":
                    path_to_image = os.path.join(
                        self.path_to_image_storage,
                        fixture_data['args']['image_id']
                    )

                    self.assertEqual(
                        disk.find("source").get("file"),
                        path_to_image
                    )

    def test_image_processing(self):
        '''
        Checks whether image file is present in
        test image storage directory
        '''
        fixture_data = {
            'image_id': '522700a8a063d875c192d818'
        }

        with patch.object(
            self.nova_mimic_instance,
            'path_to_image_storage',
            self.path_to_image_storage
        ):
            self.nova_mimic_instance._image_processing(**fixture_data)

        # check whether image was supplied for the project
        path_to_image = os.path.join(
            self.path_to_image_storage,
            fixture_data['image_id']
        )

        self.assertTrue(
            os.path.exists(path_to_image)
        )

    def test_vm_boot(self):
        '''
        Models full process of booting vm, i.e.:
        creation of xml, downloading image from key-value
        storage, booting domain.

        Checks whether vm is booted by getting connection
        to proper libvirt driver and performing lookup by
        name.

        Checks presence of domain object in domains pool.

        Checks data base (table instance) for row
        that corresponds to booted vm.
        '''

        fixture_data = {
            'instance_name': 'test_instance',
            'image_id': '522700a8a063d875c192d818',
            'flavor_id': 1
        }

        with patch.object(
            self.nova_mimic_instance,
            'path_to_image_storage',
            self.path_to_image_storage
        ):
            self.nova_mimic_instance.instance_boot(**fixture_data)

            #check if xml config was properly defined
            self.assertTrue(
                fixture_data['instance_name'] in
                self.libvirt_conn.listDefinedDomains()
            )

            #check if domain is booted
            domain = self.libvirt_conn.lookupByName(
                fixture_data['instance_name']
            )

            self.assertIsNotNone(domain)

            #check domains_pool
            self.assertIsNotNone(
                self.nova_mimic_instance.domains_pool.get(
                    fixture_data['instance_name']
                )
            )

            #check data base values
            with contexted_session() as s:
                #exception handling was added
                #just for the sake of refreshing knowleges
                try:
                    instance = s.query(Instance)\
                                .filter_by(id=domain.UUIDString())\
                                .one()
                except (NoResultFound, MultipleResultsFound):
                    raise MyException(
                        "More then one entry for instance was found"
                    )
                finally:
                    #cleaning up
                    domain.destroy()

                #check mac address that should not be available
                instance_mac_addr = s.query(MacAddress)\
                                     .join(Instance)\
                                     .filter(Instance.id == instance.id)\
                                     .one()

                self.assertFalse(instance_mac_addr.is_free)


if __name__ == '__file__':
    unittest.main()
