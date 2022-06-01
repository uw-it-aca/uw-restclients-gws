# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


"""
This is the interface for interacting with the Group Web Service.
"""

from datetime import datetime
from copy import deepcopy
import json
import logging
import re
from urllib.parse import urlencode
from restclients_core.exceptions import DataFailureException
from uw_gws.dao import GWS_DAO
from uw_gws.models import (
    Group, CourseGroup, GroupReference, GroupEntity, GroupMember,
    GroupAffiliate, GroupHistory)
from uw_gws.exceptions import InvalidGroupID


class GWS(object):
    """
    The GWS object has methods for getting group information.
    """
    API = '/group_sws/v3'
    QTRS = {'win': 'winter', 'spr': 'spring', 'sum': 'summer', 'aut': 'autumn'}
    RE_GROUP_ID = re.compile(r'^[a-z0-9][\w\.-]+$', re.I)

    def __init__(self, act_as=None, log_errors=False):
        self.DAO = GWS_DAO()
        self.act_as = act_as
        self.logger = logging.getLogger(__name__) if log_errors else None

    def search_groups(self, **kwargs):
        """
        Returns a list of restclients.GroupReference objects matching the
        passed parameters. Valid parameters are:
            name: parts_of_name
                name may include the wild-card (*) character.
            stem: group_stem
            member: member netid
            owner: admin netid
            instructor: instructor netid
                stem="course" will be set when this parameter is passed.
            student: student netid
                stem="course" will be set when this parameter is passed.
            affiliate: affiliate_name
            type: search_type
                Values are 'direct' to search for direct membership and
                'effective' to search for effective memberships. Default is
                direct membership.
            scope: search_scope
                Values are 'one' to limit results to one level of stem name
                and 'all' to return all groups.
        """
        kwargs = dict((k.lower(), kwargs[k].lower()) for k in kwargs)
        if 'type' in kwargs and (
                kwargs['type'] != 'direct' and kwargs['type'] != 'effective'):
            del(kwargs['type'])

        if 'scope' in kwargs and (
                kwargs['scope'] != 'one' and kwargs['scope'] != 'all'):
            del(kwargs['scope'])

        if "instructor" in kwargs or "student" in kwargs:
            kwargs["stem"] = "course"

        url = "{}/search?{}".format(self.API, urlencode(kwargs))

        data = self._get_resource(url)

        groups = []
        for datum in data.get('data', []):
            group = GroupReference(uwregid=datum.get('regid'),
                                   name=datum.get('id'),
                                   url=datum.get('url'))
            if datum.get('displayName') is not None:
                group.display_name = datum.get('displayName')
            else:
                group.display_name = datum.get('name')
            groups.append(group)

        return groups

    def get_group_by_id(self, group_id):
        """
        Returns a restclients.Group object for the group identified by the
        passed group ID.
        """
        self._valid_group_id(group_id)

        url = "{}/group/{}".format(self.API, group_id)

        data = self._get_resource(url)

        return self._group_from_json(data.get("data"))

    def create_group(self, group):
        """
        Creates a group from the passed restclients.Group object.
        """
        self._valid_group_id(group.name)

        body = {"data": group.json_data(is_put_req=True)}
        url = "{}/group/{}".format(self.API, group.name)

        data = self._put_resource(url, headers={}, body=body)

        return self._group_from_json(data.get("data"))

    def update_group(self, group):
        """
        Updates a group from the passed restclients.Group object.
        """
        self._valid_group_id(group.name)

        body = {"data": group.json_data(is_put_req=True)}
        headers = {"If-Match": "*"}
        url = "{}/group/{}".format(self.API, group.name)

        data = self._put_resource(url, headers, body)

        return self._group_from_json(data.get("data"))

    def delete_group(self, group_id):
        """
        Deletes the group identified by the passed group ID.
        """
        self._valid_group_id(group_id)

        url = "{}/group/{}".format(self.API, group_id)

        self._delete_resource(url)

        return True

    def get_members(self, group_id):
        """
        Returns a list of restclients.GroupMember objects for the group
        identified by the passed group ID.
        """
        self._valid_group_id(group_id)

        url = "{}/group/{}/member".format(self.API, group_id)

        data = self._get_resource(url)

        members = []
        for datum in data.get("data"):
            members.append(self._group_member_from_json(datum))
        return members

    def add_members(self, group_id, members):
        """
        Adds members into the group identified by group_id
        :param members: a non-empty list of uwnetids
        """
        self._valid_group_id(group_id)

        headers = {"If-Match": "*"}
        url = "{}/group/{}/member/{}".format(
            self.API, group_id, ",".join(members))

        self._put_resource(url, headers)

        return True

    def delete_members(self, group_id, members):
        """
        Deletes members from the group identified by group_id
        :param members: a non-empty list of uwnetids
        """
        self._valid_group_id(group_id)

        url = "{}/group/{}/member/{}".format(
            self.API, group_id, ",".join(members))

        self._delete_resource(url)

        return True

    def update_members(self, group_id, members):
        """
        Updates the membership of the group represented by the passed group id.
        Returns a list of members not found.
        """
        self._valid_group_id(group_id)

        body = {"data": [m.json_data(is_put_req=True) for m in members]}
        headers = {"If-Match": "*"}
        url = "{}/group/{}/member".format(self.API, group_id)

        data = self._put_resource(url, headers, body)

        errors = data.get("errors", [])
        if len(errors):
            return errors[0].get("notFound", [])
        return []

    def get_group_history(self, group_id,
                          activity=None,
                          start=0,
                          id=None):
        """
        Returns a list of GroupHistory objects, in the order of
        from the earliest to the latest.
        :param start: Epoch timestamp in seconds
        :param activity: one of {"acl", "membership"}
        :param id: member ID selector
        """
        kwargs = {}
        if activity:
            kwargs['activity'] = activity
        if start:
            kwargs['start'] = start * 1000
        if id:
            kwargs['id'] = id
        url = "{}/group/{}/history".format(self.API, group_id)
        self._valid_group_id(group_id)
        if len(kwargs):
            url = "{}?{}".format(url, urlencode(kwargs))
        data = self._get_resource(url)
        changes = []
        for datum in data.get("data"):
            changes.insert(0, GroupHistory(data=datum))
        return changes

    def get_effective_members(self, group_id):
        """
        Returns a list of effective restclients.GroupMember objects for the
        group identified by the passed group ID.
        """
        self._valid_group_id(group_id)

        url = "{}/group/{}/effective_member".format(self.API, group_id)

        data = self._get_resource(url)

        members = []
        for datum in data.get("data"):
            members.append(self._group_member_from_json(datum))
        return members

    def get_effective_member_count(self, group_id):
        """
        Returns a count of effective members for the group identified by the
        passed group ID.
        """
        self._valid_group_id(group_id)

        url = "{}/group/{}/effective_member?view=count".format(self.API,
                                                               group_id)

        data = self._get_resource(url)

        count = data.get("data").get("count")
        return int(count)

    def is_effective_member(self, group_id, netid):
        """
        Returns True if the netid is in the group, False otherwise.
        """
        return self.is_member(group_id, netid, True)

    def is_direct_member(self, group_id, netid):
        """
        Returns True if the netid is in the group, False otherwise.
        """
        return self.is_member(group_id, netid, False)

    def is_member(self, group_id, netid, is_effective):
        self._valid_group_id(group_id)

        # GWS doesn't accept EPPNs on effective member checks, for UW users
        netid = re.sub('@washington.edu', '', netid)
        url = "{}/group/{}/{}/{}".format(
            self.API, group_id,
            "effective_member" if is_effective else "member", netid)

        # Not using _get_resource() here because it automatically logs 404s
        response = self.DAO.getURL(url, self._headers())

        if response.status == 200:
            return True
        elif response.status == 404:
            return False
        else:
            self._log_error(url, response)
            raise DataFailureException(url, response.status, response.data)

    def _group_entity_from_json(self, data):
        return GroupEntity(name=data.get('id'),
                           type=data.get('type'),
                           display_name=data.get('name'))

    def _group_member_from_json(self, data):
        member = GroupMember(name=data.get('id'), type=data.get('type'))
        if data.get('mtype', None):
            member.mtype = data.get('mtype')
        if data.get('source', None):
            member.source = data.get('source')
        return member

    def _group_from_json(self, data):
        def _add_dt(timestamp):
            return datetime.fromtimestamp(float(timestamp)/1000.0)

        def _add_users(data, name, target):
            for item in data.get(name, []):
                target.append(self._group_entity_from_json(item))

        group_id = data.get('id')
        if re.match(r'^course_', group_id):
            course_data = data.get('course')
            group = CourseGroup()
            group.curriculum_abbr = course_data.get('curriculum')
            group.course_number = course_data.get('number')
            group.year = course_data.get('year')
            group.quarter = self.QTRS.get(course_data.get('quarter'))
            group.section_id = course_data.get('section')
            group.sln = course_data.get('sln')
            _add_users(course_data, 'instructors', group.instructors)
        else:
            group = Group()

        group.name = group_id
        group.uwregid = data.get('regid')
        group.display_name = data.get('displayName')
        group.description = data.get('description')
        group.contact = data.get('contact')
        group.authnfactor = data.get('authnfactor')
        group.classification = data.get('classification')
        group.dependson = data.get('dependson')

        try:
            group.last_modified = _add_dt(data.get('lastModified'))
        except (AttributeError, TypeError):
            pass

        try:
            group.membership_modified = _add_dt(data.get('lastMemberModified'))
        except (AttributeError, TypeError):
            pass

        _add_users(data, 'admins', group.admins)
        _add_users(data, 'updaters', group.updaters)
        _add_users(data, 'creators', group.creators)
        _add_users(data, 'readers', group.readers)
        _add_users(data, 'optins', group.optins)
        _add_users(data, 'optouts', group.optouts)

        for affl_data in data.get('affiliates'):
            affiliate = GroupAffiliate()
            affiliate.name = affl_data.get('name')
            affiliate.status = affl_data.get('status')
            affiliate.forward = affl_data.get('forward')
            _add_users(affl_data, 'sender', affiliate.senders)
            group.affiliates.append(affiliate)

        return group

    def _valid_group_id(self, group_id):
        if (group_id is None or not self.RE_GROUP_ID.match(group_id)):
            raise InvalidGroupID(group_id)

    def _get_resource(self, url):
        response = self.DAO.getURL(url, self._headers())

        if response.status != 200:
            self._log_error(url, response)
            raise DataFailureException(url, response.status, response.data)

        return json.loads(response.data)

    def _put_resource(self, url, headers, body={}):
        headers["Content-Type"] = "application/json"
        headers.update(self._headers())

        response = self.DAO.putURL(url, headers, json.dumps(body))

        if response.status != 200 and response.status != 201:
            self._log_error(url, response)
            raise DataFailureException(url, response.status, response.data)

        return json.loads(response.data)

    def _delete_resource(self, url):
        response = self.DAO.deleteURL(url, self._headers())

        if response.status != 200:
            self._log_error(url, response)
            raise DataFailureException(url, response.status, response.data)

        return json.loads(response.data)

    def _headers(self):
        headers = {"Accept": "application/json", "Connection": "keep-alive"}

        if self.act_as:
            headers["X-UW-Act-as"] = self.act_as

        return headers

    def _log_error(self, url, response):
        if self.logger:
            self.logger.error(
                "url: {0}, status: {1}, data: {2}, act_as: {3}".format(
                    url, response.status, response.data, self.act_as))
