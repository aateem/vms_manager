#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import unittest
import xml.etree.ElementTree as ElementTree

from mock import patch, Mock

import src.nova_mimic
from src.database_toolkit import Flavor, Image, MacAddress, Instance, contexted_session

#directory where data (i.e. xml config and image) will be stored
PATH_TO_TEST_PROJECTS_DIR = os.path.abspath(os.path.dirname(__file__))


@patch('src.nova_mimic.PROJECTS_PATH', PATH_TO_TEST_PROJECTS_DIR)
class TestNovaMimicBootMethod(unittest.TestCase):
    nova_mimic_instance = src.nova_mimic.NovaMimic()

    #TODO: unified fixture data
    fixture_data = ['test_instance', 1, 1]
    image_name = 'ubuntu12.04server.img'

    def tearDown(self):
        '''
        Removes test project. This action consists in
        removing xml configuration file, image file and
        project subdir
        '''
        if os.path.exists(self.path_to_xml_config):
            os.remove(self.path_to_project_subdir)

        if os.path.exists(self.path_to_image):
            os.remove(self.path_to_image)

        if os.path.exists(self.path_to_project_subdir):
            os.rmdir(self.path_to_project_subdir)

    def test_xml_config_creation(self):
        '''
        Checks whether xml config for instance is created (exists in
        test directory) and has proper values in needed sections.

        Also mocks NovaMimic._image_processing for the sake of
        keeping life clean.
        '''

        with patch.object(self.nova_mimic_instance, '_image_processing', Mock()):
            self.nova_mimic_instance.instance_boot(*self.fixture_data)

        # check whether separate directory for project was created
        self.path_to_project_subdir = os.path.join(
            PATH_TO_TEST_PROJECTS_DIR,
            self.fixture_data[0]
        )

        self.assertTrue(
            os.path.exists(path_to_project_subdir)
        )

        # check whether xml config for instance was created
        self.path_to_xml_config = os.path.join(
            path_to_project_subdir,
            '{0}.xml'.format(self.fixture_data[0])
        )

        self.assertTrue(
            os.path.exists(path_to_xml_config)
        )

        # query data from db to compare against corresponding values in config
        with contexted_session() as s:
            flavor = s.query(Flavor).filter(Flavor.id == self.fixture_data[1]).one()
            image = s.query(Image).filter(Image.id == self.fixture_data[2]).one()

            # parse xml config
            config = ElementTree.parse(path_to_xml_config)
            conf_root = config.getroot()

            # check consistency
            name = conf_root.find("name")
            self.assertEqual(name.text, self.fixture_data[0])

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
                        path_to_project_subdir,
                        "{0}.img".format(image.name)
                    )

                    self.assertEqual(
                        disk.find("source").get("file"),
                        path_to_image
                    )

    def test_image_processing(self):
        '''
        Checks whether image file is present in test projects subdir.

        Mocks NovaMimic._xml_processing for the sake
        of keeping life clean.
        '''
        with patch.object(self.nova_mimic_instance, '_xml_processing', Mock()):
            self.nova_mimic_instance.instance_boot(*self.fixture_data)

        # check whether separate directory for project was created
        self.path_to_project_subdir = os.path.join(
            PATH_TO_TEST_PROJECTS_DIR,
            self.fixture_data[0]
        )

        self.assertTrue(
            os.path.exists(path_to_project_subdir)
        )

        # check whether xml config for instance was created
        self.path_to_image = os.path.join(
            path_to_project_subdir,
            self.image_name
        )

        self.assertTrue(
            os.path.exists(path_to_image)
        )


if __name__ == '__file__':
    unittest.main()
