from restclients_core import models
import json
import time


class GWSModel(models.Model):
    def __str__(self):
        return json.dumps(self.json_data(), indent=4)


class GroupReference(GWSModel):
    name = models.CharField(max_length=500)
    uwregid = models.CharField(max_length=32)
    display_name = models.CharField(max_length=500)
    url = models.CharField(max_length=200)

    def json_data(self):
        return {
            "id": self.name,
            "regid": self.uwregid,
            "displayName": self.display_name,
            "url": self.url,
        }

    def __init__(self, *args, **kwargs):
        super(GroupReference, self).__init__(*args, **kwargs)


class Group(GWSModel):
    CLASSIFICATION_NONE = "u"
    CLASSIFICATION_RESTRICTED = "r"
    CLASSIFICATION_CONFIDENTIAL = "c"

    CLASSIFICATION_TYPES = (
        (CLASSIFICATION_NONE, "Unclassified"),
        (CLASSIFICATION_RESTRICTED, "Restricted"),
        (CLASSIFICATION_CONFIDENTIAL, "Confidential")
    )

    name = models.CharField(max_length=500)
    uwregid = models.CharField(max_length=32)
    display_name = models.CharField(max_length=500)
    description = models.CharField(max_length=2000, null=True)
    contact = models.CharField(max_length=120, null=True)
    last_modified = models.DateTimeField(null=True)
    membership_modified = models.DateTimeField(null=True)
    authnfactor = models.PositiveSmallIntegerField(
        choices=((0, ""), (1, ""), (2, "")), default=1)
    classification = models.CharField(
        max_length=1, choices=CLASSIFICATION_TYPES, null=True)
    dependson = models.CharField(max_length=500, null=True)

    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)
        self.admins = []
        self.creators = []
        self.optins = []
        self.optouts = []
        self.readers = []
        self.updaters = []
        self.affiliates = []

    def _to_timestamp(self, dt):
        if dt is not None:
            return int(time.mktime(dt.timetuple())*1000 + dt.microsecond/1000)

    def has_regid(self):
        return self.uwregid is not None and len(self.uwregid) == 32

    def json_data(self, is_put_req=False):
        data = {
            "id": self.name,
            "regid": self.uwregid,
            "displayName": self.display_name,
            "description": self.description,
            "lastModified": self._to_timestamp(self.last_modified),
            "lastMemberModified": self._to_timestamp(self.membership_modified),
            "contact": self.contact,
            "authnfactor": int(self.authnfactor),
            "classification": self.classification,
            "dependson": self.dependson,
            "admins": [e.json_data(is_put_req=is_put_req)
                       for e in self.admins],
            "updaters": [e.json_data(is_put_req=is_put_req)
                         for e in self.updaters],
            "creators": [e.json_data(is_put_req=is_put_req)
                         for e in self.creators],
            "readers": [e.json_data(is_put_req=is_put_req)
                        for e in self.readers],
            "optins": [e.json_data(is_put_req=is_put_req)
                       for e in self.optins],
            "optouts": [e.json_data(is_put_req=is_put_req)
                        for e in self.optouts],
            "affiliates": [a.json_data() for a in self.affiliates],
        }
        if is_put_req is False:
            return data
        return {k: v for k, v in data.items() if v is not None and v != ''}


class CourseGroup(Group):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"

    QUARTERNAME_CHOICES = (
        (SPRING, "Spring"),
        (SUMMER, "Summer"),
        (AUTUMN, "Autumn"),
        (WINTER, "Winter"),
    )

    curriculum_abbr = models.CharField(max_length=8)
    course_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    quarter = models.CharField(max_length=6, choices=QUARTERNAME_CHOICES)
    section_id = models.CharField(max_length=2, db_index=True)
    sln = models.PositiveIntegerField()

    def __init__(self, *args, **kwargs):
        super(CourseGroup, self).__init__(*args, **kwargs)
        self.instructors = []

    def json_data(self):
        data = super(CourseGroup, self).json_data()
        data["course"] = {
            "quarter": self.quarter[:3],
            "year": int(self.year),
            "curriculum": self.curriculum_abbr.lower(),
            "number": int(self.course_number),
            "section": self.section_id.lower(),
            "sln": self.sln,
            "instructors": [i.json_data() for i in self.instructors],
        }
        return data


class GroupEntity(GWSModel):
    UWNETID_TYPE = "uwnetid"
    EPPN_TYPE = "eppn"
    GROUP_TYPE = "group"
    DNS_TYPE = "dns"
    SET_TYPE = "set"
    UWWI_TYPE = "uwwi"

    TYPE_CHOICES = (
        (UWNETID_TYPE, "UWNetID"),
        (EPPN_TYPE, "ePPN"),
        (GROUP_TYPE, "Group ID"),
        (DNS_TYPE, "Hostname"),
        (SET_TYPE, "Set"),
        (UWWI_TYPE, "UWWI"),
    )

    name = models.CharField(max_length=50)
    display_name = models.CharField(max_length=500, null=True)
    type = models.SlugField(max_length=8, choices=TYPE_CHOICES)

    def is_uwnetid(self):
        return self.type == self.UWNETID_TYPE

    def is_eppn(self):
        return self.type == self.EPPN_TYPE

    def is_group(self):
        return self.type == self.GROUP_TYPE

    def json_data(self, is_put_req=False):
        data = {"id": self.name,
                "type": self.type}
        if is_put_req is False:
            data["name"] = self.display_name
        return data

    def __eq__(self, other):
        return self.name == other.name and self.type == other.type

    def __init__(self, *args, **kwargs):
        super(GroupEntity, self).__init__(*args, **kwargs)


class GroupMember(GroupEntity):
    DIRECT_MTYPE = "direct"
    INDIRECT_MTYPE = "indirect"

    MTYPE_CHOICES = (
        (DIRECT_MTYPE, DIRECT_MTYPE),
        (INDIRECT_MTYPE, INDIRECT_MTYPE),
    )

    mtype = models.SlugField(
        max_length=10, choices=MTYPE_CHOICES, default=DIRECT_MTYPE)
    source = models.CharField(max_length=1000, null=True)

    def json_data(self, is_put_req=False):
        data = {"id": self.name,
                "type": self.type}
        if is_put_req is False:
            data["mtype"] = self.mtype
            data["source"] = self.source
        return data

    def __init__(self, *args, **kwargs):
        super(GroupMember, self).__init__(*args, **kwargs)


class GroupAffiliate(GWSModel):
    UWNETID_NAME = "uwnetid"
    GOOGLE_NAME = "google"
    EMAIL_NAME = "email"
    RADIUS_NAME = "radius"

    NAME_CHOICES = (
        (UWNETID_NAME, "UWNetID"),
        (GOOGLE_NAME, "Google"),
        (EMAIL_NAME, "Email"),
        (RADIUS_NAME, "Radius"),
    )

    ACTIVE_STATUS = "active"
    INACTIVE_STATUS = "inactive"

    STATUS_CHOICES = (
        (ACTIVE_STATUS, ACTIVE_STATUS),
        (INACTIVE_STATUS, INACTIVE_STATUS),
    )

    name = models.CharField(max_length=20, choices=NAME_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    forward = models.CharField(max_length=50)

    def __init__(self, *args, **kwargs):
        super(GWSModel, self).__init__(*args, **kwargs)
        self.senders = []

    def is_active(self):
        return self.status == self.ACTIVE_STATUS

    def json_data(self):
        return {
            "name": self.name,
            "status": self.status,
            "forward": self.forward,
            "sender": [s.json_data() for s in self.senders],
        }
