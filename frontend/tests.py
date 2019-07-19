from django.test import TestCase

from frontend.models import Practice
from frontend.models import Group
from frontend.models import GroupKind
from frontend.models import Coding


class BasicModelTests(TestCase):
    def test_practice_groups_and_codes(self):
        ccg_kind = GroupKind.objects.create(name="ccg")
        ccg = Group.objects.create(name="My CCG", kind=ccg_kind)
        Coding(content_object=ccg, system="ods", code="RG5").save()

        practice = Practice.objects.create(name="My practice")
        practice.groups.add(ccg)
        Coding(content_object=practice, system="ods", code="A81723").save()

        self.assertEqual(
            Practice.objects.get(codes__system="ods", codes__code="A81723"), practice
        )
        self.assertEqual(str(practice.groups.first().codes.first()), "ods/RG5")
