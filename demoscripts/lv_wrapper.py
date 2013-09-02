#!/usr/bin python
# -*- coding: utf-8 -*-

import libvirt


class LVWrapper():

    def __init__(self):
        # pool of domains that are managing
        self.domains_pool = {}
        self.libvirt_connection = libvirt.open("qemu:///system")

    def get_domain_list(self):
        # display list of domains
        print self.libvirt_connection.listDefinedDomains()

    def register_domain(self):
        pass

    def boot_domain(self, domain_name):
        # boot domain with given name
        # returns id of booted domain
        domain = self.libvirt_connection.lookupByName(domain_name)
        domain.create()

        self.domains_pool[domain_name] = domain

        return domain.ID()

    def reboot_domain(self, domain_name):
        # check whether there is domain in domaing pool with such name
        # and reboots it reboot domain in way which is preferrable by libvirt
        if self.domains_pool.get(domain_name):
            return self.domains_pool[domain_name].reboot(0)

    def destroy_domain(self, domain_name):
        # check whether there is domain in domains pool with given name
        # and shutdown it (destroy) with cleaning up pool of domains
        return_code = -1
        if self.domains_pool.get(domain_name):
            return_code = self.domains_pool[domain_name].destroy()

            del(self.domains_pool[domain_name])

        return return_code

    def clean_up(self):
        # closes connection to libvirt driver
        self.libvirt_connection.close()
