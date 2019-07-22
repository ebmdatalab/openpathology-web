import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from frontend.models import Practice
from frontend.models import Group
from frontend.models import GroupKind
from frontend.models import Coding


def _get_or_create_group(system, code, name, kind):
    try:
        group = Group.objects.get(codes__system=system, codes__code=code)
        if group.name != name:
            group.name = name
            group.save()
        if group.kind != kind:
            group.kind = kind
            group.save()
    except Group.DoesNotExist:
        group = Group.objects.create(name=name, kind=kind)
        Coding(content_object=group, system=system, code=code).save()
    return group


def _get_or_create_practice(ods_code, name):
    try:
        practice = Practice.objects.get(codes__system="ods", codes__code=ods_code)
        if practice.name != name:
            practice.name = name
            practice.save()
    except Practice.DoesNotExist:
        practice = Practice.objects.create(name=name)
        Coding(content_object=practice, system="ods", code=ods_code).save()
    return practice


class Command(BaseCommand):
    """Imports a CSV of practices with their lab/CCG membership
    """

    args = ""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--filename")

    def handle(self, *args, **options):
        if "filename" not in options:
            raise CommandError("Please supply a filename")

        reader = csv.DictReader(open(options["filename"], "rU"))

        sections = {}
        with transaction.atomic():
            ccg_kind, _ = GroupKind.objects.get_or_create(name="ccg")
            lab_kind, _ = GroupKind.objects.get_or_create(name="lab")

            for row in reader:
                ccg = _get_or_create_group(
                    "ods", row["ccg_ods_code"], row["ccg_name"], ccg_kind
                )
                ccg.name = row["ccg_name"]
                ccg.save()
                lab = _get_or_create_group(
                    "lab", row["lab_code"], row["lab_name"], lab_kind
                )
                lab.name = row["lab_name"]
                practice = _get_or_create_practice(
                    row["practice_ods_code"], row["practice_name"]
                )
