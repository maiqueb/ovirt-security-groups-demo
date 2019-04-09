#!/bin/python
# Copyright 2019 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license

import getopt
import json
import logging
import openstack
import sys


logging.basicConfig(level=logging.ERROR, filename='openstack_client.log')

CLOUD_CONFIG_NAME='ovirt'
DEFAULT_VERIFY=False


def usage():
    print('Usage: {}'.format(sys.argv[0]))
    print('\t-h, --help\t\t\tdisplay this help')
    print('\t-p, --list-logical-ports\tlist logical ports')
    print('\t-s, --list-sec-groups\t\tlist security groups')


def get_connection_object(ca_path=None):
    return openstack.connect(
        cloud=CLOUD_CONFIG_NAME,
        verify=ca_path or DEFAULT_VERIFY
    )


def list_logical_ports(conn):
    print('LOGICAL PORTS:')
    for port in conn.network.ports():
        print(entity_to_json(port))


def list_security_groups(conn):
    print('SECURITY GROUPS:')
    for sec_group in conn.network.security_groups():
        print(entity_to_json(sec_group))


def entity_to_json(openstack_entity, indentation=4):
    return json.dumps(openstack_entity.to_dict(), indent=indentation)


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(
                sys.argv[1:], 'hps',
                ['help', 'list-sec-groups', 'list-logical-ports']
        )
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(1)
    if not opts:
        usage()
        sys.exit(1)

    conn = get_connection_object()
    for option, _ in opts:
        if option in ('-h', '--help'):
            usage()
            sys.exit()
        elif option in ('-p', '--list-logical-ports'):
            list_logical_ports(conn)
        elif option in ('-s', '--list-sec-groups'):
            list_security_groups(conn)

