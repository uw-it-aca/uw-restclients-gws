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

    def _edit_mock_response(self, method, url, headers, body, response):
        if "POST" == method or "PUT" == method:
            if response.status != 400:
                path = "%s/resources/gws/file%s.%s" % (
                    abspath(dirname(__file__)), url, method)
                try:
                    handle = open(path)
                    response.data = handle.read()
                    response.status = 200
                except IOError:
                    response.status = 404
