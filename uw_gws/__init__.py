"""
This is the interface for interacting with the Group Web Service.
"""

from uw_gws.dao import GWS_DAO
from uw_gws.models import (
    Group, CourseGroup, GroupReference, GroupUser, GroupMember)
from uw_gws.exceptions import InvalidGroupID
from restclients_core.exceptions import DataFailureException
from jinja2 import Environment, FileSystemLoader
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
from lxml import etree
from datetime import datetime
import re
import os


class GWS(object):
    """
    The GWS object has methods for getting group information.
    """
    QTRS = {'win': 'winter', 'spr': 'spring', 'sum': 'summer', 'aut': 'autumn'}

    def __init__(self, config={}):
        self.actas = config['actas'] if 'actas' in config else None
        self.templates = os.path.join(os.path.dirname(__file__), "templates/")

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

        dao = GWS_DAO()
        url = "/group_sws/v2/search?" + urlencode(kwargs)
        response = dao.getURL(url, self._headers({"Accept": "text/xhtml"}))

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        root = etree.fromstring(response.data)
        group_elements = root.findall(
            './/*[@class="groupreferences"]//*[@class="groupreference"]')

        groups = []
        for element in group_elements:
            group = GroupReference()
            group.uwregid = element.find('.//*[@class="regid"]').text
            group.title = element.find('.//*[@class="title"]').text
            group.description = element.find('.//*[@class="description"]').text
            group.name = element.find('.//*[@class="name"]').text
            group.url = element.find('.//*[@class="name"]').get('href')
            groups.append(group)

        return groups

    def get_group_by_id(self, group_id):
        """
        Returns a restclients.Group object for the group identified by the
        passed group ID.
        """
        if not self._is_valid_group_id(group_id):
            raise InvalidGroupID(group_id)

        dao = GWS_DAO()
        url = "/group_sws/v2/group/%s" % group_id
        response = dao.getURL(url, self._headers({"Accept": "text/xhtml"}))

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._group_from_xhtml(response.data)

    def create_group(self, group):
        """
        Creates a group from the passed restclients.Group object.
        """
        body = self._xhtml_from_group(group)
        headers = {"Accept": "text/xhtml", "Content-Type": "text/xhtml"}

        dao = GWS_DAO()
        url = "/group_sws/v2/group/%s" % group.name
        response = dao.putURL(url, self._headers(headers), body)

        if response.status != 201:
            raise DataFailureException(url, response.status, response.data)

        return self._group_from_xhtml(response.data)

    def update_group(self, group):
        """
        Updates a group from the passed restclients.Group object.
        """
        body = self._xhtml_from_group(group)
        headers = {"Accept": "text/xhtml",
                   "Content-Type": "text/xhtml",
                   "If-Match": "*"}

        dao = GWS_DAO()
        url = "/group_sws/v2/group/%s" % group.name
        response = dao.putURL(url, self._headers(headers), body)

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._group_from_xhtml(response.data)

    def delete_group(self, group_id):
        """
        Deletes the group identified by the passed group ID.
        """
        if not self._is_valid_group_id(group_id):
            raise InvalidGroupID(group_id)

        dao = GWS_DAO()
        url = "/group_sws/v2/group/%s" % group_id
        response = dao.deleteURL(url, self._headers({}))

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return True

    def get_members(self, group_id):
        """
        Returns a list of restclients.GroupMember objects for the group
        identified by the passed group ID.
        """
        if not self._is_valid_group_id(group_id):
            raise InvalidGroupID(group_id)

        dao = GWS_DAO()
        url = "/group_sws/v2/group/%s/member" % group_id
        response = dao.getURL(url, self._headers({"Accept": "text/xhtml"}))

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._members_from_xhtml(response.data)

    def update_members(self, group_id, members):
        """
        Updates the membership of the group represented by the passed group id.
        Returns a list of members not found.
        """
        if not self._is_valid_group_id(group_id):
            raise InvalidGroupID(group_id)

        body = self._xhtml_from_members(group_id, members)
        headers = {"Content-Type": "text/xhtml", "If-Match": "*"}

        dao = GWS_DAO()
        url = "/group_sws/v2/group/%s/member" % group_id
        response = dao.putURL(url, self._headers(headers), body)

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._notfoundmembers_from_xhtml(response.data)

    def get_effective_members(self, group_id):
        """
        Returns a list of effective restclients.GroupMember objects for the
        group identified by the passed group ID.
        """
        if not self._is_valid_group_id(group_id):
            raise InvalidGroupID(group_id)

        dao = GWS_DAO()
        url = "/group_sws/v2/group/%s/effective_member" % group_id
        response = dao.getURL(url, self._headers({"Accept": "text/xhtml"}))

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._effective_members_from_xhtml(response.data)

    def get_effective_member_count(self, group_id):
        """
        Returns a count of effective members for the group identified by the
        passed group ID.
        """
        if not self._is_valid_group_id(group_id):
            raise InvalidGroupID(group_id)

        dao = GWS_DAO()
        url = "/group_sws/v2/group/%s/effective_member?view=count" % group_id
        response = dao.getURL(url, self._headers({"Accept": "text/xhtml"}))

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        root = etree.fromstring(response.data)
        count = root.find('.//*[@class="member_count"]').get("count")

        return int(count)

    def is_effective_member(self, group_id, netid):
        """
        Returns True if the netid is in the group, False otherwise.
        """
        if not self._is_valid_group_id(group_id):
            raise InvalidGroupID(group_id)

        # GWS doesn't accept EPPNs on effective member checks, for UW users
        netid = re.sub('@washington.edu', '', netid)

        dao = GWS_DAO()
        url = "/group_sws/v2/group/%s/effective_member/%s" % (group_id, netid)
        response = dao.getURL(url, self._headers({"Accept": "text/xhtml"}))

        if response.status == 404:
            return False
        elif response.status == 200:
            return True
        else:
            raise DataFailureException(url, response.status, response.data)

    def _group_from_xhtml(self, data):
        root = etree.fromstring(data)
        group_id = root.find('.//*[@class="name"]').text
        if re.match(r'^course_', group_id):
            group = CourseGroup()
            group.curriculum_abbr = root.find(
                './/*[@class="course_curr"]').text.upper()
            group.course_number = root.find('.//*[@class="course_no"]').text
            group.year = root.find('.//*[@class="course_year"]').text
            group.quarter = self.QTRS[
                root.find('.//*[@class="course_qtr"]').text]
            group.section_id = root.find(
                './/*[@class="course_sect"]').text.upper()
            group.sln = root.find('.//*[@class="course_sln"]').text

            group.instructors = []
            instructors = root.findall('.//*[@class="course_instructors"]' +
                                       '/*[@class="course_instructor"]')
            for instructor in instructors:
                group.instructors.append(GroupMember(name=instructor.text,
                                                     member_type="uwnetid"))
        else:
            group = Group()

        group.name = group_id
        group.uwregid = root.find('.//*[@class="regid"]').text
        group.title = root.find('.//*[@class="title"]').text
        group.description = root.find('.//*[@class="description"]').text
        group.contact = root.find('.//*[@class="contact"]').text
        group.authnfactor = root.find('.//*[@class="authnfactor"]').text
        group.classification = root.find('.//*[@class="classification"]').text
        group.emailenabled = root.find('.//*[@class="emailenabled"]').text
        group.dependson = root.find('.//*[@class="dependson"]').text
        group.publishemail = root.find('.//*[@class="publishemail"]').text

        try:
            member_modified = root.find('.//*[@class="membermodifytime"]').text
            group.membership_modified = datetime.fromtimestamp(
                float(member_modified)/1000)
        except AttributeError:
            group.membership_modified = None

        try:
            group.reporttoorig = root.find('.//*[@class="reporttoorig"]').text
        except AttributeError:
            # Legacy class name for this attribute
            group.reporttoorig = root.find('.//*[@class="reporttoowner"]').text

        for user in root.findall('.//*[@class="admins"]/*[@class="admin"]'):
            group.admins.append(GroupUser(name=user.text,
                                          user_type=user.get("type")))

        for user in (
                root.findall('.//*[@class="updaters"]/*[@class="updater"]')):
            group.updaters.append(GroupUser(name=user.text,
                                            user_type=user.get("type")))

        for user in (
                root.findall('.//*[@class="creators"]/*[@class="creator"]')):
            group.creators.append(GroupUser(name=user.text,
                                            user_type=user.get("type")))

        for user in root.findall('.//*[@class="readers"]/*[@class="reader"]'):
            group.readers.append(GroupUser(name=user.text,
                                           user_type=user.get("type")))

        for user in root.findall('.//*[@class="optins"]/*[@class="optin"]'):
            group.optins.append(GroupUser(name=user.text,
                                          user_type=user.get("type")))

        for user in root.findall('.//*[@class="optouts"]/*[@class="optout"]'):
            group.optouts.append(GroupUser(name=user.text,
                                           user_type=user.get("type")))

        # viewers are not used according to Jim Fox
        group.viewers = []
        for user in root.findall('.//*[@class="viewers"]/*[@class="viewer"]'):
            group.viewers.append(GroupUser(name=user.text,
                                           user_type=user.get("type")))
        return group

    def _effective_members_from_xhtml(self, data):
        root = etree.fromstring(data)
        member_elements = root.findall(
            './/*[@class="members"]//*[@class="effective_member"]')

        members = []
        for member in member_elements:
            members.append(GroupMember(name=member.text,
                                       member_type=member.get("type")))

        return members

    def _members_from_xhtml(self, data):
        root = etree.fromstring(data)
        member_elements = root.findall(
            './/*[@class="members"]//*[@class="member"]')

        members = []
        for member in member_elements:
            members.append(GroupMember(name=member.text,
                                       member_type=member.get("type")))

        return members

    def _notfoundmembers_from_xhtml(self, data):
        root = etree.fromstring(data)
        member_elements = root.findall(
            './/*[@class="notfoundmembers"]//*[@class="notfoundmember"]')

        members = []
        for member in member_elements:
            members.append(member.text)

        return members

    def _is_valid_group_id(self, group_id):
        if (group_id is None or
                not re.match(r'^[a-z0-9][\w\.-]+$', group_id, re.I)):
            return False

        return True

    def _headers(self, headers):
        if self.actas:
            headers = self._add_header(headers, "X-UW-Act-as", self.actas)
        return headers

    def _add_header(self, headers, header, value):
        if not headers:
            return {header: value}

        headers[header] = value
        return headers

    def _xhtml_from_group(self, group):
        return self._render_template("group.xhtml", context={"group": group})

    def _xhtml_from_members(self, group_id, members):
        return self._render_template(
            "members.xhtml",
            context={"group_id": group_id, "members": members})

    def _render_template(self, template, context={}):
        return Environment(
                loader=FileSystemLoader(self.templates)
            ).get_template(template).render(context)
