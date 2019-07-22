import glob
import os

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.db.models import Q

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

    class Manager(models.Manager):
        def filter_by_entity_code(self, code_filter):
            code_system, code = code_filter.split("/")
            return Practice.objects.filter(
                (Q(codes__system=code_system) & Q(codes__code=code))
                | (Q(groups__codes__system=code_system) & Q(groups__codes__code=code))
            )

        def get_by_entity_code(self, code_filter):
            return self.filter_by_entity_code(code_filter).get()

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
    objects = Manager()

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


def _sorted_files_at_glob(file_name_glob):
    # The final part of the filename, when split by underscore, is
    # a sort key generated when the chart is created
    files = sorted(
        glob.glob(file_name_glob), key=lambda filename: filename.split("_")[-1]
    )
    return [os.path.relpath(x, start=settings.PREGENERATED_CHARTS_ROOT) for x in files]


class Measure(models.Model):
    id = models.CharField(max_length=40, primary_key=True)
    title = models.CharField(max_length=500)
    why_it_matters = models.TextField(null=True, blank=True)

    def chart_urls_for_all(self, ods_practice_codes=None):
        """Return list of URLs for pregenerated charts for every practice

        """
        file_name_glob = "*_*_*.png"
        file_name_glob = os.path.join(
            settings.PREGENERATED_CHARTS_ROOT, "*", file_name_glob
        )
        urls = _sorted_files_at_glob(file_name_glob)
        if ods_practice_codes:
            matched = []
            for must_match in ods_practice_codes:
                for url in urls:
                    if "_{}_".format(must_match) in url:
                        matched.append(url)
                        continue
            urls = matched
        return urls

    def __str__(self):
        return self.title
