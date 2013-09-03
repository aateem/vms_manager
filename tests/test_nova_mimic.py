#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
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

#directory where data (i.e. xml config and image) will be stored
PATH_TO_TEST_PROJECTS_DIR = os.path.abspath(os.path.dirname(__file__))


#just for remembering exception handling
class MyException(Exception):
    pass


@patch('src.nova_mimic.PROJECTS_PATH', PATH_TO_TEST_PROJECTS_DIR)
class TestNovaMimicBootMethod(unittest.TestCase):
    def setUp(self):
        self.libvirt_conn = libvirt.open("qemu:///system")
        self.nova_mimic_instance = src.nova_mimic.NovaMimic()

        #creating project subdir
        self.project_name = 'test_instance'
        self.project_subdir_path = os.path.join(
            PATH_TO_TEST_PROJECTS_DIR,
            self.project_name
        )

    def tearDown(self):
        '''
        Removes test project. This action consists in
        removing project subdir.

        Closes connectin to libvirt driver.
        '''
        if os.path.exists(self.project_subdir_path):
            os.rmdir(self.project_subdir_path)

        self.libvirt_conn.close()

    def test_manage_project_path(self):
        self.nova_mimic_instance._manage_project_path(self.project_name)

        self.assertEqual(
            self.nova_mimic_instance.current_project_path,
            self.project_subdir_path
        )

    def test_xml_processing(self):
        '''
        Checks whether xml config for instance is created (exists in
        test directory) and has proper values in needed sections.
        '''
        fixture_data = {
            'args':
            {
                'instance_name': self.project_name,
                'image_name': 'ubuntu12.04server',
                'memory': 524288,
                'vcpu': 1,
                'mac_address': '52:54:00:83:df:a1'
            },
            'image_id': 1,
            'flavor_id': 1
        }

        if not os.path.exists(self.project_subdir_path):
            os.mkdir(self.project_subdir_path)

        with patch.object(self.nova_mimic_instance, 'current_project_path', self.project_subdir_path, create=True):
            produced_path = self.nova_mimic_instance._xml_processing(
                **fixture_data['args']
            )

        # check whether xml config for instance was created
        path_to_xml_config = os.path.join(
            self.project_subdir_path,
            '{0}.xml'.format(fixture_data['args']['instance_name'])
        )

        self.assertTrue(
            os.path.exists(path_to_xml_config)
        )

        #check that produced path is equal to real path
        self.assertEqual(produced_path, path_to_xml_config)

        # query data from db to compare against corresponding values in config
        with contexted_session() as s:
            flavor = s.query(Flavor)\
                      .filter(Flavor.id == fixture_data['flavor_id'])\
                      .one()

            image = s.query(Image)\
                     .filter(Image.id == fixture_data['image_id'])\
                     .one()

            # parse xml config
            config = ElementTree.parse(path_to_xml_config)
            conf_root = config.getroot()

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
                        self.project_subdir_path,
                        "{0}.img".format(fixture_data['args']['image_name'])
                    )

                    self.assertEqual(
                        disk.find("source").get("file"),
                        path_to_image
                    )

        #cleaning
        if os.path.exists(path_to_xml_config):
            os.remove(path_to_xml_config)

    def test_image_processing(self):
        '''
        Checks whether image file is present in test projects subdir.
        '''
        fixture_data = {
            'image_name': 'ubuntu12.04server',
            'storage_key': '52247faca063d808024e5f96'
        }

        #hence _image_processing method is tested in isolation
        #we must mock behaviour of all code which it depends on

        #here we create needed directory on filesystem
        if not os.path.exists(self.project_subdir_path):
            os.mkdir(self.project_subdir_path)

        #here we created mocked attribute for nova_mimic_instance
        #which is supplied by another method of instance but must be available
        #in this test
        with patch.object(self.nova_mimic_instance, 'current_project_path', self.project_subdir_path, create=True):
            self.nova_mimic_instance._image_processing(**fixture_data)

        # check whether image was supplied for the project
        path_to_image = os.path.join(
            self.project_subdir_path,
            "{0}.img".format(fixture_data['image_name'])
        )

        self.assertTrue(
            os.path.exists(path_to_image)
        )

        #cleaning
        if os.path.exists(path_to_image):
            os.remove(path_to_image)

    def test_vm_boot(self):
        '''
        Checks whether xml config for domain was
        defined properly.

        Checks whether vm is booted by getting connection
        to proper libvirt driver and performing lookup by
        name.

        Checks presence of domain object in domains pool.

        Checks data base (table instance) for row
        that corresponds to booted vm.
        '''

        fixture_data = {
            'instance_name': self.project_name,
            'image_id': 1,
            'flavor_id': 1
        }

        with patch.dict(self.nova_mimic_instance.domains_pool):
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
                                .filter(Instance.id == domain.UUIDString())\
                                .one()
                except (NoResultFound, MultipleResultsFound):
                    raise MyException(
                        "There should be only one entry in data base for instance"
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
