#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import patch, Mock
import unittest
import src.nova_mimic


@patch('src.nova_mimic.PROJECTS_PATH', new='mocked_path')
class TestPatch(unittest.TestCase):
    def test_method(self):
        print src.nova_mimic.PROJECTS_PATH
        self.assertEqual(src.nova_mimic.PROJECTS_PATH, 'mocked_path')


class TestPatchContext(unittest.TestCase):
    def test_method(self):
        with patch('src.nova_mimic.PROJECTS_PATH', new='mocked_path'):
            print src.nova_mimic.PROJECTS_PATH
            print src.nova_mimic.XML_PATTERN_FOR_INSTANCE
            self.assertEqual(src.nova_mimic.PROJECTS_PATH, 'mocked_path')


if __name__ == '__main__':
    unittest.main()
