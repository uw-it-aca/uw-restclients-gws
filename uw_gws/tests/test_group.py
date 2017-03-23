from unittest import TestCase
from uw_gws import GWS
from uw_gws.models import Group, CourseGroup, GroupUser, GroupMember
from uw_gws.utilities import fdao_gws_override
from uw_gws.exceptions import InvalidGroupID
from restclients_core.exceptions import DataFailureException


@fdao_gws_override
class GWSGroupTest(TestCase):
    def test_get_nonexistant_group(self):
        gws = GWS()
        self.assertRaises(DataFailureException,
                          gws.get_group_by_id,
                          "u_acadev_nonexistant_tester")

        self.assertRaises(InvalidGroupID, gws.get_group_by_id, None)
        self.assertRaises(InvalidGroupID, gws.get_group_by_id, "")

    def test_get_group(self):
        gws = GWS()
        group = gws.get_group_by_id('u_acadev_tester')
        self.assertEquals(group.name, "u_acadev_tester")

    def test_get_course_group(self):
        gws = GWS()
        group = gws.get_group_by_id("course_2012aut-train102a")
        self.assertEquals(group.name, "course_2012aut-train102a")
        self.assertEquals(group.curriculum_abbr, "TRAIN")
        self.assertEquals(group.course_number, "102")
        self.assertEquals(group.section_id, "A")
        self.assertEquals(group.year, "2012")
        self.assertEquals(group.quarter, "autumn")

    def test_create_group(self):
        gws = GWS()
        group = Group(name="u_acadev_tester2",
                      title="New ACA Tester")
        group.admins = [GroupUser(user_type="uwnetid", name="acadev")]
        group.readers = [GroupUser(user_type="none", name="dc=all")]

        new_group = gws._group_from_xhtml(gws._xhtml_from_group(group))

        self.assertEquals(new_group.title, group.title)

    def test_update_group(self):
        gws = GWS()
        group = gws.get_group_by_id("u_acadev_tester")
        group.title = "ACA Tester"

        new_group = gws._group_from_xhtml(gws._xhtml_from_group(group))

        self.assertEquals(new_group.title, group.title)

    def test_delete_group(self):
        gws = GWS()
        group = Group(name='u_acadev_tester')
        result = gws.delete_group(group.name)
        self.assertEquals(result, True)

    def test_group_membership(self):
        gws = GWS()
        members = gws.get_members('u_acadev_unittest')
        self.assertEquals(len(members), 2)

    def test_update_members(self):
        gws = GWS()
        members = gws.get_members('u_acadev_unittest')

        self.assertEquals(len(members), 2)

        members.remove(GroupMember(member_type="uwnetid", name="eight"))

        new_members = gws._members_from_xhtml(
            gws._xhtml_from_members('u_acadev_unittest', members))

        self.assertEquals(len(new_members), 1)

        members.append(GroupMember(member_type="uwnetid", name="seven"))
        members.append(GroupMember(member_type="uwnetid", name="eight"))
        members.append(GroupMember(member_type="uwnetid", name="nine"))

        new_members = gws._members_from_xhtml(
            gws._xhtml_from_members('u_acadev_unittest', members))

        self.assertEquals(len(new_members), 4)

    def test_effective_group_membership(self):
        gws = GWS()
        members = gws.get_effective_members('u_acadev_unittest')

        self.assertEquals(len(members), 3)
        has_pmichaud = False
        has_javerage = False
        has_eight = False

        for member in members:
            if member.name == "pmichaud":
                has_pmichaud = True
            elif member.name == "javerage":
                has_javerage = True
            elif member.name == "eight":
                has_eight = True

        self.assertEquals(has_pmichaud, True)
        self.assertEquals(has_javerage, True)
        self.assertEquals(has_eight, True)

        count = gws.get_effective_member_count('u_acadev_unittest')
        self.assertEquals(count, 3)

    def test_is_effective_member(self):
        gws = GWS()

        self.assertEquals(
            gws.is_effective_member('u_acadev_unittest', 'pmichaud'), True)
        self.assertEquals(
            gws.is_effective_member('u_acadev_unittest',
                                    'pmichaud@washington.edu'), True)
        self.assertEquals(
            gws.is_effective_member('u_acadev_unittest', 'javerage'), True)
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

    def test_group_roles(self):
        group = GWS().get_group_by_id('u_eventcal_sea_1013649-editor')

        self.assertEquals(group.name, "u_eventcal_sea_1013649-editor")
        self.assertEquals(group.uwregid, "143bc3d173d244f6a2c3ced159ba9c97")
        self.assertEquals(
            group.title, "College of Arts and Sciences calendar editor group")
        self.assertEquals(group.description, (
            "Specifying the editors who are able to add/edit/delete any "
            "event on the corresponding Seattle Trumba calendar"))

        self.assertIsNotNone(group.admins)
        self.assertEquals(len(group.admins), 1)
        self.assertEquals(group.admins[0].user_type, GroupUser.GROUP_TYPE)
        self.assertEquals(group.admins[0].name, "u_eventcal_support")

        self.assertIsNotNone(group.updaters)
        self.assertEquals(len(group.updaters), 1)
        self.assertEquals(group.updaters[0].user_type, GroupUser.GROUP_TYPE)
        self.assertEquals(
            group.updaters[0].name, "u_eventcal_sea_1013649-editor")

        self.assertIsNotNone(group.readers)
        self.assertEquals(len(group.readers), 1)
        self.assertEquals(group.readers[0].user_type, GroupUser.NONE_TYPE)
        self.assertEquals(group.readers[0].name, "dc=all")

        self.assertIsNotNone(group.optouts)
        self.assertEquals(len(group.optouts), 1)
        self.assertEquals(group.optouts[0].user_type, GroupUser.NONE_TYPE)
        self.assertEquals(group.optouts[0].name, "dc=all")
