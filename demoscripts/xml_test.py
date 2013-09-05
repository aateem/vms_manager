#!/usr/bin/python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET

document = ET.parse('domain_pattern.xml')
root = document.getroot()

name = root.find('name')
name.text = 'Some_custom_name'

memory = root.find('memory')
memory.text = str(512)

root.find('currentMemory').text = str(512)

root.find('vcpu').text = str(1)

# path to image
devices = root.find('devices')

for disk in devices.findall('disk'):
    if disk.get('type') == 'file':
        disk.find('source').set('file', '/home/aroma/Programming/sandbox/test/data/pattern_for_lv_wrapper.img')

print type(document)
document.write('test_xml.xml', encoding='utf-8')
