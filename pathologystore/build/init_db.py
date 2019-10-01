"""
Sets up a SQLite database ready to have prescribing data and practice
statistics imported into it.

Data on practices and presentations is obtained by connecting to BigQuery.
"""
import logging
import os
import sqlite3

from django.contrib.contenttypes.models import ContentType

from common.constants import RESULT_CATEGORIES
from frontend.models import Coding, Practice

from .common import get_temp_filename
from .dates import generate_dates


logger = logging.getLogger(__name__)


SCHEMA_SQL = """
    CREATE TABLE labtest (
        test_code TEXT,
        -- The below columns will contain the test result data as serialized
        -- matrices of shape (number of practices, number of months)
        {data_columns}

        PRIMARY KEY (test_code)
    );

    -- Maps each practice code to its corresponding row offset in the data matrix
    CREATE TABLE practice (
        offset INTEGER,
        code TEXT UNIQUE,

        PRIMARY KEY (offset)
    );

    -- Maps each date to its corresponding column offset in the data matrix
    CREATE TABLE date (
        offset INTEGER,
        date TEXT UNIQUE,

        PRIMARY KEY (offset)
    );
""".format(
    data_columns='\n        '.join([
        '{} BLOB,'.format(name) for (_, name, _) in RESULT_CATEGORIES
    ])
)


def init_db(end_date, sqlite_path, months=None):
    if os.path.exists(sqlite_path):
        raise RuntimeError("File already exists at: " + sqlite_path)
    logger.info("Initialising SQLite database at %s", sqlite_path)
    sqlite_path = os.path.abspath(sqlite_path)
    temp_filename = get_temp_filename(sqlite_path)
    sqlite_conn = sqlite3.connect(temp_filename)
    sqlite_conn.executescript(SCHEMA_SQL)
    dates = generate_dates(end_date, months=months)
    import_dates(sqlite_conn, dates)
    practice_codes = sorted(get_all_practice_codes())
    import_practices(practice_codes, sqlite_conn)
    sqlite_conn.commit()
    sqlite_conn.close()
    os.rename(temp_filename, sqlite_path)


def get_all_practice_codes():
    practice_type = ContentType.objects.get_for_model(Practice)
    return (
        Coding.objects
        .filter(
            system='ods', content_type=practice_type
        )
        .order_by('code')
        .values_list('code', flat=True)
    )


def import_dates(sqlite_conn, dates):
    sqlite_conn.executemany(
        "INSERT INTO date (offset, date) VALUES (?, ?)", enumerate(dates)
    )


def import_practices(practice_codes, sqlite_conn):
    logger.info("Writing %s practice codes to SQLite", len(practice_codes))
    sqlite_conn.executemany(
        "INSERT INTO practice (offset, code) VALUES (?, ?)", enumerate(practice_codes)
    )
