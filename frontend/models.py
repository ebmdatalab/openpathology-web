from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models

from common.utils import nhs_titlecase


class Coding(models.Model):
    """All entities in the system have a code which is unique as a (system, code) tuple
    """

    system = models.CharField(max_length=200, db_index=True)
    code = models.CharField(max_length=50, db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["system", "code"], name="system_and_code_unique_together"
            )
        ]

    def __str__(self):
        return "{}/{}".format(self.system, self.code)


class GroupKind(models.Model):
    name = models.CharField(max_length=200)


class Group(models.Model):
    name = models.CharField(max_length=200)
    kind = models.ForeignKey(GroupKind, on_delete=models.PROTECT)
    codes = GenericRelation(Coding, related_query_name="group")
    boundary = models.GeometryField(null=True, blank=True, srid=4326)
    open_date = models.DateField(null=True, blank=True)
    close_date = models.DateField(null=True, blank=True)


class Practice(models.Model):
    """
    GP practices
    """

    PRESCRIBING_SETTINGS = (
        (-1, "Unknown"),
        (0, "Other"),
        (1, "WIC Practice"),
        (2, "OOH Practice"),
        (3, "WIC + OOH Practice"),
        (4, "GP Practice"),
        (8, "Public Health Service"),
        (9, "Community Health Service"),
        (10, "Hospital Service"),
        (11, "Optometry Service"),
        (12, "Urgent & Emergency Care"),
        (13, "Hospice"),
        (14, "Care Home / Nursing Home"),
        (15, "Border Force"),
        (16, "Young Offender Institution"),
        (17, "Secure Training Centre"),
        (18, "Secure Children's Home"),
        (19, "Immigration Removal Centre"),
        (20, "Court"),
        (21, "Police Custody"),
        (22, "Sexual Assault Referral Centre (SARC)"),
        (24, "Other - Justice Estate"),
        (25, "Prison"),
    )

    STATUS_RETIRED = "B"
    STATUS_CLOSED = "C"
    STATUS_DORMANT = "D"

    STATUS_SETTINGS = (
        ("U", "Unknown"),
        ("A", "Active"),
        (STATUS_RETIRED, "Retired"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_DORMANT, "Dormant"),
        ("P", "Proposed"),
    )
    codes = GenericRelation(Coding, related_query_name="practice")
    groups = models.ManyToManyField(Group)
    name = models.CharField(max_length=200)
    address1 = models.CharField(max_length=200, null=True, blank=True)
    address2 = models.CharField(max_length=200, null=True, blank=True)
    address3 = models.CharField(max_length=200, null=True, blank=True)
    address4 = models.CharField(max_length=200, null=True, blank=True)
    address5 = models.CharField(max_length=200, null=True, blank=True)
    postcode = models.CharField(max_length=9, null=True, blank=True)
    location = models.PointField(null=True, blank=True, srid=4326)
    boundary = models.GeometryField(null=True, blank=True, srid=4326)
    setting = models.IntegerField(choices=PRESCRIBING_SETTINGS, default=-1)
    open_date = models.DateField(null=True, blank=True)
    close_date = models.DateField(null=True, blank=True)
    status_code = models.CharField(
        max_length=1, choices=STATUS_SETTINGS, null=True, blank=True
    )

    def __str__(self):
        return self.name

    @property
    def cased_name(self):
        return nhs_titlecase(self.name)

    def is_inactive(self):
        return self.status_code in (
            self.STATUS_RETIRED,
            self.STATUS_DORMANT,
            self.STATUS_CLOSED,
        )

    def inactive_status_suffix(self):
        if self.is_inactive():
            return " - {}".format(self.get_status_code_display())
        else:
            return ""

    def address_pretty(self):
        address = self.address1 + ", "
        if self.address2:
            address += self.address2 + ", "
        if self.address3:
            address += self.address3 + ", "
        if self.address4:
            address += self.address4 + ", "
        if self.address5:
            address += self.address5 + ", "
        address += self.postcode
        return address

    def address_pretty_minus_firstline(self):
        address = ""
        if self.address2:
            address += self.address2 + ", "
        if self.address3:
            address += self.address3 + ", "
        if self.address4:
            address += self.address4 + ", "
        if self.address5:
            address += self.address5 + ", "
        address += self.postcode
        return address
