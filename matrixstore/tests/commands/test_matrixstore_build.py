"""
This tests the MatrixStore build process:

    `TestMatrixStoreBuild` runs entirely in memory and therefore shortcuts
    various parts of the build process which involve downloading data from
    BigQuery

    'TestMatrixStoreBuildEndToEnd` runs the same set of tests but uploads data
    to BigQuery and exports it to Google Cloud Storage in order to excercise
    the full build process

The end-to-end test contains an additional check whereby it builds a file using
the fast process and checks that the resulting SQL dump is identical to that
produced by the full end-to-end process.
"""
from __future__ import print_function

from collections import defaultdict
import os
import json
import numbers
import shutil
import sqlite3
import tempfile

from django.test import SimpleTestCase

import numpy

from matrixstore.serializer import deserialize
from matrixstore.tests.data_factory import DataFactory
from matrixstore.tests.import_test_data_fast import import_test_data_fast
from matrixstore.tests.import_test_data_full import import_test_data_full


class TestMatrixStoreBuild(SimpleTestCase):
    """
    Runs a test of the MatrixStore build process entirely in memory
    """

    @classmethod
    def setUpClass(cls):
        factory = DataFactory()
        cls.months = factory.create_months("2019-01-01", 3)
        # This practice won't do any prescribing but it will have practice
        # statistics so it should still show up in our data
        cls.non_testing_practice = factory.create_practice()
        # Create some practices that prescribe during the period
        cls.testing_practices = factory.create_practices(3)
        # Create some presentations and some prescribing
        cls.tests = factory.create_tests(4)
        cls.test_results = factory.create_test_results(
            cls.tests, cls.testing_practices, cls.months
        )
        # Create practices statistics for all active practices
        cls.active_practices = cls.testing_practices + [cls.non_testing_practice]
        cls.practice_statistics = factory.create_practice_statistics(
            cls.active_practices, cls.months
        )
        # Create a presentation without creating any test for it so we can
        # check it doesn't appear in the final file
        cls.test_without_test_result = factory.create_test()
        # We deliberately import data for fewer months than we've created so we
        # can test that only the right data is included
        cls.months_to_import = cls.months[1:]
        # This practice only has data for the month we don't import, so it
        # shouldn't show up at all in our data
        cls.closed_practice = factory.create_practice()
        factory.create_test_result(cls.tests[0], cls.closed_practice, cls.months[0])
        factory.create_statistics_for_one_practice_and_month(
            cls.closed_practice, cls.months[0]
        )
        cls.data_factory = factory
        # The format of `end_date` only uses year and month
        cls.end_date = max(cls.months_to_import)[:7]
        cls.number_of_months = len(cls.months_to_import)
        cls.create_matrixstore(factory, cls.end_date, cls.number_of_months)

    @classmethod
    def create_matrixstore(cls, data_factory, end_date, number_of_months):
        cls.connection = sqlite3.connect(":memory:")
        import_test_data_fast(
            cls.connection, data_factory, end_date, months=number_of_months
        )

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def setUp(self):
        # Reset this as at least one test modifies it
        self.connection.row_factory = None

    def test_dates_are_correct(self):
        dates = [
            row[0]
            for row in self.connection.execute("SELECT date FROM date ORDER BY offset")
        ]
        expected_dates = [date[:10] for date in self.months_to_import]
        self.assertEqual(dates, expected_dates)

    def test_practices_are_correct(self):
        practice_codes = [
            row[0]
            for row in self.connection.execute(
                "SELECT code FROM practice ORDER BY code"
            )
        ]
        expected_codes = sorted(
            [practice["code"] for practice in self.active_practices]
        )
        self.assertEqual(practice_codes, expected_codes)
        self.assertNotIn(self.closed_practice["code"], practice_codes)

    def test_tests_are_correct(self):
        """I think this checks the expectation that just because we create
        tests, they don't end up in the database when there is no data
        for them

        """
        expected = list(self.tests)
        expected.sort(key=lambda i: i["test_code"])
        # Allow us to get results as dicts
        self.connection.row_factory = sqlite3.Row
        results = self.connection.execute(
            """
            SELECT DISTINCT
              test_code
            FROM
              tests
            ORDER BY
              test_code
            """
        )
        results = [dict(row) for row in results]
        self.assertEqual(results, expected)
        self.assertNotIn(self.test_without_test_result, results)

    def test_practice_statistics_are_correct(self):
        get_value = MatrixValueFetcher(
            self.connection, "practice_statistic", "name", "value"
        )
        expected_entries = 0
        for entry in self.practice_statistics:
            practice = entry["practice"]
            month = entry["month"]
            if month not in self.months_to_import:
                continue
            for field, expected_value in entry.items():
                if field in ("month", "practice", "pct_id", "star_pu"):
                    continue
                expected_entries += 1
                value = get_value(field, practice, month)
                self.assertEqual(value, expected_value)
        # Check there are no additional values that we weren't expecting
        self.assertEqual(get_value.nonzero_values, expected_entries)

    def test_test_values_are_correct(self):
        for field in ["count"]:
            # Cost figures are originally in pounds but we store them in pence
            # as ints
            get_value = MatrixValueFetcher(self.connection, "tests", "test_code", field)
            expected_entries = 0
            for entry in self._expected_test_results():
                expected_entries += 1
                value = get_value(entry["test_code"], entry["practice"], entry["month"])
                expected_value = round(entry[field])
                self.assertEqual(value, expected_value)
            # Check there are no additional values that we weren't expecting
            self.assertEqual(get_value.nonzero_values, expected_entries)

    def _expected_test_results(self):
        import pdb

        pdb.set_trace()

        for entry in self.test_results:
            if entry["month"] in self.months_to_import:
                yield entry


class TestMatrixStoreBuildEndTtsoEnd(TestMatrixStoreBuild):
    """
    Runs the same test as above but as a full integration test against actual
    BigQuery and Google Cloud Storage. Also checks that the fast build process
    produces an identical file to the full process.
    """

    @classmethod
    def create_matrixstore(cls, data_factory, end_date, number_of_months):
        cls.tempdir = tempfile.mkdtemp()
        # Upload data to BigQuery and build file
        cls.data_file = import_test_data_full(
            cls.tempdir, data_factory, end_date, months=number_of_months
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    def setUp(self):
        # We have to check this because the `sqlite3.connect` call will
        # implicitly create the file if it doesn't exist
        if not os.path.exists(self.data_file):
            raise RuntimeError("No SQLite file created")
        self.connection = sqlite3.connect(self.data_file)

    def tearDown(self):
        self.connection.close()

    def test_same_file_produced_by_import_test_data_fast(self):
        other_connection = sqlite3.connect(":memory:")
        import_test_data_fast(
            other_connection, self.data_factory, self.end_date, self.number_of_months
        )
        db_dump = list(self.connection.iterdump())
        other_db_dump = list(other_connection.iterdump())
        self.assertEqual(db_dump, other_db_dump)


class MatrixValueFetcher(object):
    """
    Provides convenient access to values stored in matrices in SQLite
    """

    def __init__(self, connection, table, key_field, value_field):
        results = connection.execute(
            "SELECT {}, {} FROM {}".format(key_field, value_field, table)
        )
        self.matrices = {}
        self.nonzero_values = 0
        for key, value in results:
            matrix = deserialize(value)
            self.matrices[key] = matrix
            if hasattr(matrix, "count_nonzero"):
                self.nonzero_values += matrix.count_nonzero()
            else:
                self.nonzero_values += numpy.count_nonzero(matrix)
        self.practices = dict(connection.execute("SELECT code, offset FROM practice"))
        self.dates = dict(connection.execute("SELECT date, offset FROM date"))
        for date, offset in list(self.dates.items()):
            self.dates[date + " 00:00:00 UTC"] = offset

    def __call__(self, key, practice, date):
        """
        Find the row in `table` where `key_field` matches `key` and extract the
        matrix stored in `value_field`. Return the value at the row and column
        corresponding to `practice` and `date`
        """
        row = self.practices[practice]
        column = self.dates[date]
        return self.matrices[key][row, column]


def sum_dicts(current_values, new_values):
    """
    Add the numeric parts of `new_values` to `current_values`
    """
    for field, value in new_values.items():
        if not isinstance(value, numbers.Number):
            continue
        zero = type(value)()
        current_values[field] = current_values.get(field, zero) + value
