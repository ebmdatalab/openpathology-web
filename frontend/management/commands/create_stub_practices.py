import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from frontend.models import Practice
from frontend.models import Coding


class Command(BaseCommand):
    """
    Create practice entries for all practice codes appearing in a lab results file

    This ensures that even if we don't have the full practce details we can
    still import the associated data.
    """
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("filename")

    def handle(self, filename, **options):
        codes_in_file = self.get_practice_codes_from_file(filename)
        with transaction.atomic():
            existing_codes = self.get_existing_practice_codes()
            new_codes = codes_in_file - existing_codes
            for code in new_codes:
                practice = Practice.objects.create(name=code)
                Coding.objects.create(content_object=practice, system="ods", code=code)

    def get_practice_codes_from_file(self, filename):
        practice_codes = set()
        with open(filename, 'rt') as f:
            reader = csv.reader(f)
            headers = next(reader)
            practice_col = headers.index('source')
            for row in reader:
                practice_codes.add(row[practice_col])
        return practice_codes

    def get_existing_practice_codes(self):
        practice_type = ContentType.objects.get_for_model(Practice)
        return set(
            Coding.objects
            .filter(
                system='ods', content_type=practice_type
            )
            .values_list('code', flat=True)
        )
