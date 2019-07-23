from unittest import TestCase
from restclients_core.exceptions import DataFailureException
from uw_gws import GWS
from uw_gws.models import (
    Group, CourseGroup, GroupEntity, GroupMember, GroupAffiliate)
from uw_gws.utilities import fdao_gws_override
from uw_gws.exceptions import InvalidGroupID
from restclients_core.exceptions import DataFailureException
import mock


@fdao_gws_override
class GWSGroupTest(TestCase):
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
        self.assertEquals(group.name, "u_acadev_tester")
        self.assertEquals(group.uwregid, "2a815628b04c4ada8fa490ea8f4364c8")
        self.assertEquals(group.display_name, "Friends and Partners of ACA")
        self.assertEquals(
            group.description,
            "Folks outside of uw-it that need access to ACA resources")
        self.assertEquals(group.contact, "javerage")
        self.assertEquals(group.authnfactor, 1)
        self.assertEquals(group.classification, "u")
        self.assertEquals(group.dependson, "")

    def test_get_course_group(self):
        gws = GWS()
        group = gws.get_group_by_id("course_2012aut-train102a")
        self.assertEquals(group.name, "course_2012aut-train102a")
        self.assertEquals(group.curriculum_abbr, "train")
        self.assertEquals(group.course_number, 102)
        self.assertEquals(group.section_id, "a")
        self.assertEquals(group.year, 2012)
        self.assertEquals(group.quarter, "autumn")
        self.assertEquals(len(group.instructors), 11)
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
        self.assertEquals(group1.name, group.name)

        json_for_creat = group.json_data(is_put_req=True)
        self.assertFalse('regid' in json_for_creat)
        self.assertFalse('description' in json_for_creat)
        self.assertFalse('lastModified' in json_for_creat)
        self.assertFalse('lastMemberModified' in json_for_creat)
        self.assertFalse('contact' in json_for_creat)
        self.assertFalse('classification' in json_for_creat)
        self.assertEquals(len(json_for_creat['admins']), 1)
        self.assertEquals(len(json_for_creat['readers']), 1)
        self.assertEquals(len(json_for_creat['optins']), 0)
        self.assertEquals(len(json_for_creat['optouts']), 0)
        self.assertEquals(len(json_for_creat['creators']), 0)
        self.assertEquals(len(json_for_creat['updaters']), 0)

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
        result = gws.delete_group(group.name)
        self.assertEquals(result, True)

    def test_group_member(self):
        member1 = GroupMember(type="uwnetid",
                              name="javerage",
                              mtype="direct")
        self.assertEquals(member1.is_uwnetid(), True)
        self.assertEquals(member1.json_data(),
                          {"type": "uwnetid",
                           "mtype": "direct",
                           "source": None,
                           "id": "javerage"})
        self.assertEquals(member1.json_data(is_put_req=True),
                          {"type": "uwnetid",
                           "id": "javerage"})
        member2 = GroupMember(type="uwnetid", name="javerage")
        self.assertEquals(member2.type, "uwnetid")
        self.assertEquals(member2.name, "javerage")
        self.assertEquals(member2.mtype, GroupMember.DIRECT_MTYPE)
        self.assertEquals(member1 == member2, True)

        member3 = GroupMember(type="eppn", name="javerage@washington.edu")
        self.assertEquals(member3.is_uwnetid(), False)
        self.assertEquals(member3.is_eppn(), True)
        self.assertEquals(member1 == member3, False)

        member4 = GroupMember(type="group", name="u_acadev_unittest")
        self.assertEquals(member4.is_uwnetid(), False)
        self.assertEquals(member4.is_group(), True)
        self.assertEquals(member1 == member4, False)

    def test_group_membership(self):
        gws = GWS()
        members = gws.get_members('u_acadev_unittest')
        self.assertEquals(len(members), 2)
        self.assertIn(GroupMember(type="uwnetid", name="eight"), members)
        self.assertNotIn(GroupMember(type="eppn", name="j@washington.edu"),
                         members)

    @mock.patch.object(GWS, '_put_resource')
    def test_update_members(self, mock_put):
        gws = GWS()
        members = gws.get_members('u_acadev_unittest')

        self.assertEquals(len(members), 2)

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

        self.assertEquals(len(bad_members), 1)

    def test_effective_group_membership(self):
        gws = GWS()
        members = gws.get_effective_members('u_acadev_unittest')

        self.assertEquals(len(members), 3)
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

        self.assertEquals(has_seven, True)
        self.assertEquals(has_javerage, True)
        self.assertEquals(has_eight, True)

        count = gws.get_effective_member_count('u_acadev_unittest')
        self.assertEquals(count, 3)

    def test_is_effective_member(self):
        gws = GWS()

        self.assertEquals(
            gws.is_effective_member('u_acadev_unittest', 'javerage'), True)
        self.assertEquals(
            gws.is_effective_member(
                'u_acadev_unittest', 'javerage@washington.edu'), True)
        self.assertEquals(
            gws.is_effective_member('u_acadev_unittest', 'eight'), True)
        self.assertEquals(
            gws.is_effective_member('u_acadev_unittest', 'not_member'), False)

    def test_group_search(self):
        gws = GWS()
        groups = gws.search_groups(member="javerage")
        self.assertEquals(len(groups), 15)

        groups = gws.search_groups(member="JAVERAGE")
        self.assertEquals(len(groups), 15)

        groups = gws.search_groups(member="javerage", type="effective")
        self.assertEquals(len(groups), 7)

        groups = gws.search_groups(stem='cal_sea')
        self.assertEquals(len(groups), 5)
        self.assertEqual(groups[0].json_data(),
                         {'displayName': 'cal_sea parent group',
                          'id': 'cal_sea',
                          'regid': 'baf5f1c40d6c4fbc80df6c8f2deeed5d',
                          'url': None})
        self.assertIsNotNone(str(groups[0]))

    def test_affiliates(self):
        group = GWS().get_group_by_id('u_acadev_unittest')
        self.assertEquals(len(group.affiliates), 0)

        group = GWS().get_group_by_id('u_acadev_tester')
        self.assertEquals(len(group.affiliates), 1)

        affiliate = group.affiliates[0]
        self.assertEquals(affiliate.name, 'google')
        self.assertEquals(affiliate.is_active(), True)
        self.assertEquals(len(affiliate.senders), 0)

    def test_group_roles(self):
        group = GWS().get_group_by_id('u_acadev_tester')

        self.assertIsNotNone(group.admins)
        self.assertEquals(len(group.admins), 2)
        self.assertIn(
            GroupEntity(name="u_javerage_admin", type=GroupEntity.GROUP_TYPE),
            group.admins)

        self.assertIsNotNone(group.updaters)
        self.assertEquals(len(group.updaters), 1)
        self.assertIn(
            GroupEntity(name="u_javerage_update", type=GroupEntity.GROUP_TYPE),
            group.updaters)

        self.assertIsNotNone(group.readers)
        self.assertEquals(len(group.readers), 1)
        self.assertIn(
            GroupEntity(name="all", type=GroupEntity.SET_TYPE),
            group.readers)

        self.assertIsNotNone(group.creators)
        self.assertEquals(len(group.creators), 1)
        self.assertIn(
            GroupEntity(name="jcreator", type=GroupEntity.UWNETID_TYPE),
            group.creators)

        self.assertIsNotNone(group.optins)
        self.assertEquals(len(group.optins), 1)
        self.assertIn(
            GroupEntity(name="joptin", type=GroupEntity.UWNETID_TYPE),
            group.optins)

        self.assertIsNotNone(group.optouts)
        self.assertEquals(len(group.optouts), 1)
        self.assertIn(
            GroupEntity(name="all", type=GroupEntity.SET_TYPE),
            group.optouts)
