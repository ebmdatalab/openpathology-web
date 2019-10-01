"""
Runs the complete process to build a SQLite file with pathology data in
MatrixStore format
"""
import logging
import os
import sqlite3

from django.core.management import BaseCommand

from pathologystore.build.common import get_temp_filename
from pathologystore.build.dates import DEFAULT_NUM_MONTHS
from pathologystore.build.init_db import init_db
from pathologystore.build.import_labresults import import_labresults


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("input_csv_file")
        parser.add_argument("output_sqlite_file")
        parser.add_argument("end_date", help="YYYY-MM format")
        parser.add_argument(
            "--months",
            help="Number of months of data to include (default: {})".format(
                DEFAULT_NUM_MONTHS
            ),
            default=DEFAULT_NUM_MONTHS,
        )
        parser.add_argument(
            "--quiet", help="Don't emit logging output", action="store_true"
        )

    def handle(
        self,
        input_csv_file,
        output_sqlite_file,
        end_date,
        months=None,
        quiet=False,
        **kwargs
    ):
        log_level = "INFO" if not quiet else "ERROR"
        with LogToStream("pathologystore", self.stdout, log_level):
            return build(input_csv_file, output_sqlite_file, end_date, months=months)


class LogToStream(object):
    """
    Context manager which captures messages sent to the named logger (and its
    children) and writes them to `stream`
    """

    def __init__(self, logger_name, stream, level):
        self.logger_name = logger_name
        self.stream = stream
        self.level = level

    def __enter__(self):
        self.logger = logging.getLogger(self.logger_name)
        self.handler = logging.StreamHandler(self.stream)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(message)s", datefmt="%H:%M:%S"
        )
        self.handler.setFormatter(formatter)
        self.previous_level = self.logger.level
        self.logger.setLevel(self.level)
        self.logger.addHandler(self.handler)

    def __exit__(self, *args):
        self.logger.setLevel(self.previous_level)
        self.logger.removeHandler(self.handler)


def build(input_csv_file, output_sqlite_file, end_date, months=None):
    sqlite_temp = get_temp_filename(output_sqlite_file)
    init_db(end_date, sqlite_temp, months=months)
    import_labresults(input_csv_file, sqlite_temp)
    vacuum_database(sqlite_temp)
    logger.info("Moving file to final location: %s", output_sqlite_file)
    os.rename(sqlite_temp, output_sqlite_file)


def vacuum_database(sqlite_path):
    """
    Rebuild the database file, repacking it into the minimal amount of space
    and ensuring that table and index data is stored contiguously

    This also has the advantage that files built with the same data should be
    byte-for-byte identical, regardless of the order in which data was
    processed.
    """
    logger.info("Vacuuming database file")
    connection = sqlite3.connect(sqlite_path)
    connection.execute("VACUUM")
    connection.commit()
    connection.close()
