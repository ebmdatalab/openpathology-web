import lxml.html
import os
from contextlib import contextmanager
from unittest.mock import patch


from django.urls import reverse
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


def create_measures():
    Measure.objects.create(id="has_no_data", title="Test Measure with no data")
    return Measure.objects.create(id="testmeasure", title="Test Measure")


@contextmanager
def create_measure_with_practices():
    ccg = create_ccg()
    practice1 = create_practice(ccg=ccg, code="01")
    practice2 = create_practice(ccg=ccg, code="02")
    measure = create_measures()
    test_measure_png_paths = [
        os.path.join(settings.PREGENERATED_CHARTS_ROOT, "testmeasure_01_02.png"),
        os.path.join(settings.PREGENERATED_CHARTS_ROOT, "testmeasure_02_01.png"),
    ]
    with chart_fixtures(test_measure_png_paths):
        yield measure


@contextmanager
def chart_fixtures(full_paths):
    """Create empty files at the specified paths; remove the files on completion.

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


class ModelTests(TestCase):
    def test_filter_by_entity_code(self):
        ccg = create_ccg()
        practice = create_practice(ccg=ccg, code="01")
        self.assertEqual(Practice.objects.get_by_entity_code("ods/01"), practice)
        self.assertEqual(
            list(Practice.objects.filter_by_entity_code("ods/RG5")), [practice]
        )
        self.assertEqual(str(practice.groups.first().codes.first()), "ods/RG5")

    @override_settings(PREGENERATED_CHARTS_ROOT="/tmp/test_charts/")
    def test_chart_urls_for_all(self):
        with create_measure_with_practices() as measure:
            self.assertEqual(
                measure.chart_urls_for_all(),
                ["testmeasure_02_01.png", "testmeasure_01_02.png"],
            )


@override_settings(
    PREGENERATED_CHARTS_ROOT="/tmp/test_charts/",
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
)
class ViewTests(TestCase):
    def test_measures(self):
        with create_measure_with_practices() as measure:
            response = self.client.get(reverse("measures"))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, measure.title)

    def test_measure_all_practices(self):
        with create_measure_with_practices() as measure:
            response = self.client.get(
                reverse("measure", kwargs={"measure": measure.id})
            )
            self.assertEqual(response.status_code, 200)
            html = lxml.html.document_fromstring(response.content)
            links = html.xpath("//img[contains(@class, 'measure-chart')]/@src")
            self.assertEqual(
                links,
                ["/static/testmeasure_02_01.png", "/static/testmeasure_01_02.png"],
            )

    def test_non_matching_measure_all_practices(self):
        with create_measure_with_practices() as measure:
            response = self.client.get(
                reverse("measure", kwargs={"measure": "has_no_data"})
            )
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'src="/static/testmeasure_01_02.png"')

    def test_measure_single_practice(self):
        with create_measure_with_practices() as measure:
            response = self.client.get(
                reverse("measure", kwargs={"measure": measure.id}) + "?filter=ods/01"
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'src="/static/testmeasure_01_02.png"')
            self.assertNotContains(response, 'src="/static/testmeasure_02_01.png"')

    def test_measure_no_matching_practices(self):
        with create_measure_with_practices() as measure:
            response = self.client.get(
                reverse("measure", kwargs={"measure": measure.id})
                + "?filter=ods/nonexistent"
            )
            html = lxml.html.document_fromstring(response.content)
            links = html.xpath("//img[contains(@class, 'measure-chart')]/@src")
            self.assertEqual(len(links), 0)
