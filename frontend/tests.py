from django.test import TestCase

from frontend.models import Practice
from frontend.models import Group
from frontend.models import GroupKind
from frontend.models import Coding


def create_ccg():
    ccg_kind = GroupKind.objects.create(name="ccg")
    ccg = Group.objects.create(name="My CCG", kind=ccg_kind)
    Coding(content_object=ccg, system="ods", code="RG5").save()
    return ccg


def create_practice(ccg=None):
    practice = Practice.objects.create(name="My practice")
    Coding(content_object=practice, system="ods", code="A81723").save()
    if ccg:
        practice.groups.add(ccg)
    return practice


class BasicModelTests(TestCase):
    def test_filter_by_entity_code(self):
        ccg = create_ccg()
        practice = create_practice(ccg=ccg)
        self.assertEqual(Practice.objects.get_by_entity_code("ods/A81723"), practice)
        self.assertEqual(
            list(Practice.objects.filter_by_entity_code("ods/RG5")), [practice]
        )
        self.assertEqual(str(practice.groups.first().codes.first()), "ods/RG5")
