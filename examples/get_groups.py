# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from commonconf.backends import use_configparser_backend
from commonconf import settings
import argparse
import os


def get_groups_owned_by(uwnetid):
    settings_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                 'settings.cfg')
    use_configparser_backend(settings_path, 'GWS')

    from uw_gws import GWS

    client = GWS()
    for group in client.search_groups(owner=uwnetid):
        print(group)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('owner', help='Find groups owned by [uwnetid]')
    args = parser.parse_args()
    get_groups_owned_by(args.owner)
