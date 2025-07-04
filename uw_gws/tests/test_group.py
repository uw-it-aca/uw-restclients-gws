# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from unittest import TestCase
from restclients_core.exceptions import DataFailureException
from uw_gws import GWS
from uw_gws.models import (
    Group, CourseGroup, GroupEntity, GroupMember, GroupAffiliate,
    GroupHistory)
from uw_gws.utilities import fdao_gws_override
from uw_gws.exceptions import InvalidGroupID
from datetime import datetime, timedelta, timezone
import mock


@fdao_gws_override
class GWSGroupTest(TestCase):
    def test_init(self):
        gws = GWS()
        self.assertIsNone(gws.logger)

        gws = GWS(log_errors=True)
        self.assertIsNotNone(gws.logger)

    def test_request_headers(self):
        gws = GWS()

        self.assertEqual(gws._headers(),
                         {'Accept': 'application/json',
                          'Connection': 'keep-alive'})

        gws = GWS(act_as='javerage')
        self.assertEqual(gws._headers(),
                         {'Accept': 'application/json',
                          'Connection': 'keep-alive',
                          'X-UW-Act-as': 'javerage'})

    def test_get_nonexistent_group(self):
        gws = GWS()
        self.assertRaises(DataFailureException,
                          gws.get_group_by_id,
                          "u_acadev_nonexistent_tester")

        self.assertRaises(InvalidGroupID, gws.get_group_by_id, None)
        self.assertRaises(InvalidGroupID, gws.get_group_by_id, "x")
        self.assertRaises(InvalidGroupID, gws.get_group_by_id, "")

    def test_get_group(self):
        gws = GWS()
        group = gws.get_group_by_id('u_acadev_tester')
        self.assertEqual(group.name, "u_acadev_tester")
        self.assertEqual(group.uwregid, "2a815628b04c4ada8fa490ea8f4364c8")
        self.assertEqual(group.display_name, "Friends and Partners of ACA")
        self.assertEqual(
            group.description,
            "Folks outside of uw-it that need access to ACA resources")
        self.assertEqual(group.contact, "javerage")
        self.assertEqual(group.authnfactor, 1)
        self.assertEqual(group.classification, "u")
        self.assertEqual(group.dependson, "")

    def test_get_course_group(self):
        gws = GWS()
        group = gws.get_group_by_id("course_2012aut-train102a")
        self.assertEqual(group.name, "course_2012aut-train102a")
        self.assertEqual(group.curriculum_abbr, "train")
        self.assertEqual(group.course_number, 102)
        self.assertEqual(group.section_id, "a")
        self.assertEqual(group.year, 2012)
        self.assertEqual(group.quarter, "autumn")
        self.assertEqual(len(group.instructors), 11)
        self.assertIsNotNone(group.json_data())

    def test_create_group(self):
        gws = GWS()
        group = Group(name="u_acadev_tester2", display_name="New ACA Tester")
        group.admins = [GroupEntity(type="uwnetid", name="acadev")]
        group.readers = [GroupEntity(type="set", name="all")]
        json_data = group.json_data()
        self.assertTrue('regid' in json_data)
        self.assertTrue('description' in json_data)
        self.assertTrue('lastModified' in json_data)
        self.assertTrue('lastMemberModified' in json_data)
        self.assertTrue('contact' in json_data)
        self.assertTrue('classification' in json_data)
        self.assertTrue('name' in json_data['admins'][0])
        group1 = gws._group_from_json(json_data)
        self.assertEqual(group1.name, group.name)

        json_for_creat = group.json_data(is_put_req=True)
        self.assertFalse('regid' in json_for_creat)
        self.assertFalse('description' in json_for_creat)
        self.assertFalse('lastModified' in json_for_creat)
        self.assertFalse('lastMemberModified' in json_for_creat)
        self.assertFalse('contact' in json_for_creat)
        self.assertFalse('classification' in json_for_creat)
        self.assertEqual(len(json_for_creat['admins']), 1)
        self.assertEqual(len(json_for_creat['readers']), 1)
        self.assertEqual(len(json_for_creat['optins']), 0)
        self.assertEqual(len(json_for_creat['optouts']), 0)
        self.assertEqual(len(json_for_creat['creators']), 0)
        self.assertEqual(len(json_for_creat['updaters']), 0)

        self.assertRaises(DataFailureException, gws.create_group, group)

    def test_update_group(self):
        gws = GWS()
        group = gws.get_group_by_id("u_acadev_tester")
        group.display_name = "ACA Tester"
        self.assertTrue(group.has_regid())
        json_for_upd = group.json_data(is_put_req=True)
        self.assertFalse("name" in json_for_upd['admins'][0])
        self.assertFalse("name" in json_for_upd['updaters'][0])
        self.assertFalse("name" in json_for_upd['creators'][0])
        self.assertFalse("name" in json_for_upd['readers'][0])
        self.assertFalse("name" in json_for_upd['optins'][0])
        self.assertFalse("name" in json_for_upd['optouts'][0])
        self.assertTrue('regid' in json_for_upd)
        self.assertTrue('description' in json_for_upd)
        self.assertTrue('lastModified' in json_for_upd)
        self.assertTrue('lastMemberModified' in json_for_upd)
        self.assertTrue('contact' in json_for_upd)
        self.assertTrue('classification' in json_for_upd)

        group1 = gws.update_group(group)
        self.assertIsNotNone(group1)

    def test_delete_group(self):
        gws = GWS()
        group = Group(name='u_acadev_tester')
        self.assertTrue(gws.delete_group(group.name))

    def test_group_member(self):
        member1 = GroupMember(type="uwnetid",
                              name="javerage",
                              mtype="direct")
        self.assertEqual(member1.is_uwnetid(), True)

        self.assertEqual(
            member1.json_data(),
            {"type": "uwnetid",
             "mtype": "direct",
             "source": None,
             "id": "javerage"})
        self.assertEqual(
            member1.json_data(is_put_req=True),
            {"type": "uwnetid",
             "id": "javerage"})

        member2 = GroupMember(type="uwnetid", name="javerage")
        self.assertEqual(member2.type, "uwnetid")
        self.assertEqual(member2.name, "javerage")
        self.assertEqual(member2.mtype, GroupMember.DIRECT_MTYPE)
        self.assertEqual(member1 == member2, True)

        member3 = GroupMember(type="eppn", name="javerage@washington.edu")
        self.assertEqual(member3.is_uwnetid(), False)
        self.assertEqual(member3.is_eppn(), True)
        self.assertEqual(member1 == member3, False)

        member4 = GroupMember(type="group", name="u_acadev_unittest")
        self.assertEqual(member4.is_uwnetid(), False)
        self.assertEqual(member4.is_group(), True)
        self.assertEqual(member1 == member4, False)

    def test_group_membership(self):
        gws = GWS()
        members = gws.get_members('u_acadev_unittest')
        self.assertEqual(len(members), 2)
        self.assertIn(GroupMember(type="uwnetid", name="eight"), members)
        self.assertNotIn(GroupMember(type="eppn", name="j@washington.edu"),
                         members)

    def test_add_members(self):
        gws = GWS()
        self.assertTrue(gws.add_members(
            'u_acadev_unittest', ['seven']))

        self.assertRaises(DataFailureException,
                          gws.add_members,
                          'u_acadev_err', ['seven'])

    def test_delete_members(self):
        gws = GWS()
        self.assertTrue(gws.delete_members(
            'u_acadev_unittest', ['eight', 'seven']))

        self.assertRaises(DataFailureException,
                          gws.delete_members,
                          'u_acadev_err', ['seven'])

    @mock.patch.object(GWS, '_put_resource')
    def test_update_members(self, mock_put):
        gws = GWS()
        members = gws.get_members('u_acadev_unittest')

        self.assertEqual(len(members), 2)

        members.remove(GroupMember(type="uwnetid", name="eight"))

        res = gws.update_members('u_acadev_unittest', members)

        mock_put.assert_called_with(
            '/group_sws/v3/group/u_acadev_unittest/member',
            {'If-Match': '*'},
            {'data': [{'type': 'uwnetid', 'id': 'javerage'}]})

        members.append(GroupMember(type="uwnetid", name="seven"))
        members.append(GroupMember(type="uwnetid", name="eight"))
        members.append(GroupMember(type="uwnetid", name="nine"))

        res = gws.update_members('u_acadev_unittest', members)

        mock_put.assert_called_with(
            '/group_sws/v3/group/u_acadev_unittest/member',
            {'If-Match': '*'},
            {'data': [{'type': 'uwnetid', 'id': 'javerage'},
                      {'type': 'uwnetid', 'id': 'seven'},
                      {'type': 'uwnetid', 'id': 'eight'},
                      {'type': 'uwnetid', 'id': 'nine'}]})

    def test_update_members_notfound(self):
        gws = GWS()

        members = []
        members.append(GroupMember(type="uwnetid", name="_"))

        bad_members = gws.update_members("u_acadev_bad_members", members)

        self.assertEqual(len(bad_members), 1)

    def test_effective_group_membership(self):
        gws = GWS()
        members = gws.get_effective_members('u_acadev_unittest')

        self.assertEqual(len(members), 3)
        has_seven = False
        has_javerage = False
        has_eight = False

        for member in members:
            if member.name == "seven":
                has_seven = True
            elif member.name == "javerage":
                has_javerage = True
            elif member.name == "eight":
                has_eight = True

        self.assertEqual(has_seven, True)
        self.assertEqual(has_javerage, True)
        self.assertEqual(has_eight, True)

        count = gws.get_effective_member_count('u_acadev_unittest')
        self.assertEqual(count, 3)

    def test_is_effective_member(self):
        gws = GWS()

        self.assertTrue(
            gws.is_effective_member('u_acadev_unittest', 'javerage'))
        self.assertEqual(
            gws.is_effective_member(
                'u_acadev_unittest', 'javerage@washington.edu'), True)
        self.assertEqual(
            gws.is_effective_member('u_acadev_unittest', 'eight'), True)
        self.assertEqual(
            gws.is_effective_member('u_acadev_unittest', 'not_member'), False)

    def test_is_direct_member(self):
        gws = GWS()

        self.assertTrue(gws.is_direct_member('u_acadev_tester', 'javerage'))
        self.assertTrue(gws.is_direct_member(
                'u_acadev_tester', 'javerage@washington.edu'))
        self.assertFalse(
            gws.is_direct_member('u_acadev_unittest', 'eight'))

    def test_group_search(self):
        gws = GWS()
        groups = gws.search_groups(member="javerage")
        self.assertEqual(len(groups), 15)

        groups = gws.search_groups(member="JAVERAGE")
        self.assertEqual(len(groups), 15)

        groups = gws.search_groups(member="javerage", type="effective")
        self.assertEqual(len(groups), 7)

        groups = gws.search_groups(stem='cal_sea')
        self.assertEqual(len(groups), 5)
        self.assertEqual(groups[0].json_data(),
                         {'displayName': 'cal_sea parent group',
                          'id': 'cal_sea',
                          'regid': 'baf5f1c40d6c4fbc80df6c8f2deeed5d',
                          'url': None})
        self.assertIsNotNone(str(groups[0]))

    def test_affiliates(self):
        group = GWS().get_group_by_id('u_acadev_unittest')
        self.assertEqual(len(group.affiliates), 0)

        group = GWS().get_group_by_id('u_acadev_tester')
        self.assertEqual(len(group.affiliates), 1)

        affiliate = group.affiliates[0]
        self.assertEqual(affiliate.name, 'google')
        self.assertEqual(affiliate.is_active(), True)
        self.assertEqual(len(affiliate.senders), 0)

    def test_group_roles(self):
        group = GWS().get_group_by_id('u_acadev_tester')

        self.assertIsNotNone(group.admins)
        self.assertEqual(len(group.admins), 2)
        self.assertIn(
            GroupEntity(name="u_javerage_admin", type=GroupEntity.GROUP_TYPE),
            group.admins)

        self.assertIsNotNone(group.updaters)
        self.assertEqual(len(group.updaters), 1)
        self.assertIn(
            GroupEntity(name="u_javerage_update", type=GroupEntity.GROUP_TYPE),
            group.updaters)

        self.assertIsNotNone(group.readers)
        self.assertEqual(len(group.readers), 1)
        self.assertIn(
            GroupEntity(name="all", type=GroupEntity.SET_TYPE),
            group.readers)

        self.assertIsNotNone(group.creators)
        self.assertEqual(len(group.creators), 1)
        self.assertIn(
            GroupEntity(name="jcreator", type=GroupEntity.UWNETID_TYPE),
            group.creators)

        self.assertIsNotNone(group.optins)
        self.assertEqual(len(group.optins), 1)
        self.assertIn(
            GroupEntity(name="joptin", type=GroupEntity.UWNETID_TYPE),
            group.optins)

        self.assertIsNotNone(group.optouts)
        self.assertEqual(len(group.optouts), 1)
        self.assertIn(
            GroupEntity(name="all", type=GroupEntity.SET_TYPE),
            group.optouts)

    def test_get_group_history(self):
        gh = GroupHistory(
            description="add member: 'five'",
            activity='membership',
            member_uwnetid="five",
            member_action="add member",
            timestamp=162621504964)
        self.assertTrue(gh.is_add_member())

        history = GWS().get_group_history('u_acadev_tester')
        self.assertEqual(len(history), 5)
        self.assertEqual(
            history[0].json_data(),
            {"description": "created: 'u_eventcal_sea_1340210-editor'",
             "activity": "group",
             "timestamp": 1626119425407,
             "member_uwnetid": None,
             "member_action": None,
             "is_add_member": None,
             "is_delete_member": None})

        # get change history of a particular member id
        changes = GWS().get_group_history(
            'u_acadev_tester', id='eight')
        self.assertEqual(len(changes), 1)
        self.assertEqual(
            changes[0].json_data(),
            {"description": "delete member: 'eight'",
             "activity": "membership",
             "member_uwnetid": "eight",
             "member_action": "delete member",
             "timestamp": 1626193233239,
             "is_add_member": False,
             "is_delete_member": True})

        # get history of membership changes since a given timestamp
        ts = datetime(2021, 7, 13, 15, 30, 00, tzinfo=timezone(
            timedelta(seconds=-7*60*60))).timestamp()
        changes = GWS().get_group_history(
            'u_acadev_tester',
            activity='membership',
            start=int(ts))
        self.assertEqual(len(changes), 2)
        self.assertEqual(
            changes[0].json_data(),
            {"description": "delete member: 'eight'",
             "activity": "membership",
             "member_uwnetid": "eight",
             "member_action": "delete member",
             "timestamp": 1626193233239,
             "is_add_member": False,
             "is_delete_member": True})
        self.assertEqual(
            changes[1].json_data(),
            {"description": "add member: 'five'",
             "activity": "membership",
             "timestamp": 1626215049643,
             "member_uwnetid": "five",
             "member_action": "add member",
             "is_add_member": True,
             "is_delete_member": False})
        self.assertIsNotNone(changes[1])
