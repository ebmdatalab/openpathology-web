import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from frontend.models import Measure


class Command(BaseCommand):
    """Imports a CSV of measures
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
            for row in reader:
                measure, _ = Measure.objects.get_or_create(id=row["id"])
                measure.title = row["title"]
                measure.why_it_matters = row["why_it_matters"]
                measure.save()
