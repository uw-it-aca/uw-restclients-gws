# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from commonconf.backends import use_configparser_backend
from commonconf import settings
import argparse
import os


def get_members(group_id):
    settings_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                 'settings.cfg')
    use_configparser_backend(settings_path, 'GWS')

    from uw_gws import GWS

    client = GWS()
    for member in client.get_members(group_id):
        print(member.name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('group_id', help='Get members for group [group_id]')
    args = parser.parse_args()
    get_members(args.group_id)
