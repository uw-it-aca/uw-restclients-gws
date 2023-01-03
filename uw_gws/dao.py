# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


"""
Contains UW GWS DAO implementations.
"""
from restclients_core.dao import DAO
from os.path import abspath, dirname
import os


class GWS_DAO(DAO):
    def service_name(self):
        return 'gws'

    def service_mock_paths(self):
        path = [abspath(os.path.join(dirname(__file__), "resources"))]
        return path
