import os
from contextlib import contextmanager

from django.conf import settings
from django.test import TestCase
from django.test import override_settings

from frontend.models import Practice
from frontend.models import Group
from frontend.models import GroupKind
from frontend.models import Coding
from frontend.models import Measure


def create_ccg():
    ccg_kind = GroupKind.objects.create(name="ccg")
    ccg = Group.objects.create(name="My CCG", kind=ccg_kind)
    Coding(content_object=ccg, system="ods", code="RG5").save()
    return ccg


def create_practice(ccg=None, code=None):
    practice = Practice.objects.create(name="My practice {}".format(code))
    Coding(content_object=practice, system="ods", code=code).save()
    if ccg:
        practice.groups.add(ccg)
    return practice


def create_measure():
    return Measure.objects.create(id="testmeasure", title="Test Measure")


@contextmanager
def chart_fixtures(full_paths):
    """Create empty files at the specified paths; remove the files and the
    directories that contain them on completion.

    """
    try:
        for full_path in full_paths:
            location, filename = os.path.split(full_path)
            os.makedirs(location, exist_ok=True)
            with open(full_path, "w") as f:
                f.write("test")
        yield

    finally:
        for full_path in full_paths:
            location, filename = os.path.split(full_path)
            os.remove(full_path)
        for full_path in full_paths:
            location, filename = os.path.split(full_path)
            if os.path.exists(location):
                os.removedirs(location)


class BasicModelTests(TestCase):
    def test_filter_by_entity_code(self):
        ccg = create_ccg()
        practice = create_practice(ccg=ccg, code="01")
        self.assertEqual(Practice.objects.get_by_entity_code("ods/01"), practice)
        self.assertEqual(
            list(Practice.objects.filter_by_entity_code("ods/RG5")), [practice]
        )
        self.assertEqual(str(practice.groups.first().codes.first()), "ods/RG5")

    @override_settings(PREGENERATED_CHARTS_ROOT="/tmp/test_charts/")
    def test_chart_url_for_practice(self):
        ccg = create_ccg()
        practice = create_practice(ccg=ccg, code="01")
        measure = create_measure()
        test_measure_png_path = os.path.join(
            settings.PREGENERATED_CHARTS_ROOT, "RG5", "testmeasure_01_23.png"
        )
        with chart_fixtures([test_measure_png_path]):
            self.assertEqual(
                measure.chart_url_for_practice("01"), "RG5/testmeasure_01_23.png"
            )

    @override_settings(PREGENERATED_CHARTS_ROOT="/tmp/test_charts/")
    def test_chart_urls_for_ccg(self):
        ccg = create_ccg()
        practice1 = create_practice(ccg=ccg, code="01")
        practice2 = create_practice(ccg=ccg, code="02")
        measure = create_measure()
        test_measure_png_paths = [
            os.path.join(
                settings.PREGENERATED_CHARTS_ROOT, "RG5", "testmeasure_01_02.png"
            ),
            os.path.join(
                settings.PREGENERATED_CHARTS_ROOT, "RG5", "testmeasure_02_01.png"
            ),
        ]
        with chart_fixtures(test_measure_png_paths):
            self.assertEqual(
                measure.chart_urls_for_ccg("RG5"),
                ["RG5/testmeasure_02_01.png", "RG5/testmeasure_01_02.png"],
            )
