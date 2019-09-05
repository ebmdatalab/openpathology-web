"""
Import prescribing data from CSV files into SQLite
"""
from collections import namedtuple
import csv
from itertools import groupby
import logging
import os
import sqlite3
import gzip
import heapq

from matrixstore.matrix_ops import sparse_matrix, finalise_matrix
from matrixstore.serializer import serialize_compressed

from .common import get_test_results_filenames
from common import constants


logger = logging.getLogger(__name__)


MatrixRow = namedtuple("MatrixRow", "test_code result_category count")


class MissingHeaderError(Exception):
    pass


def import_test_results(filename):
    if not os.path.exists(filename):
        raise RuntimeError("No SQLite file at: {}".format(filename))
    connection = sqlite3.connect(filename)
    # Trade crash-safety for insert speed
    connection.execute("PRAGMA synchronous=OFF")
    dates = [date for (date,) in connection.execute("SELECT date FROM date")]
    test_results = get_test_results_for_dates(dates)
    write_test_results(connection, test_results)
    connection.commit()
    connection.close()


def write_test_results(connection, test_results):
    cursor = connection.cursor()
    # Map practice codes and date strings to their corresponding row/column
    # offset in the matrix
    practices = dict(cursor.execute("SELECT code, offset FROM practice"))
    dates = dict(cursor.execute("SELECT date, offset FROM date"))
    matrices = build_matrices(test_results, practices, dates)
    rows = format_as_sql_rows(matrices, connection)
    cursor.executemany(
        """
        UPDATE tests SET count=?
        WHERE test_code=? AND result_category=?
        """,
        rows,
    )


def delete_tests_with_no_results(cursor):
    cursor.execute("DELETE FROM tests WHERE count IS NULL")


def get_test_results_for_dates(dates):
    """
    Yield all test_results data for the given dates as tuples of the form:

        test_code, practice_code, date, count

    sorted by test_code, practice and date.
    """
    dates = sorted(dates)
    filenames = set()
    for date in dates:
        filenames.update(get_test_results_filenames(date))
    test_results_streams = [read_gzipped_test_results_csv(f) for f in filenames]
    # We assume that the input files are already sorted by (test_code,
    # category, practice, month) so to ensure that the combined stream
    # is sorted we just need to merge them correctly, which
    # heapq.merge handles nicely for us
    return heapq.merge(*test_results_streams)


def read_gzipped_test_results_csv(filename):
    with gzip.open(filename, "rb") as f:
        for row in parse_test_results_csv(f):
            yield row


def parse_test_results_csv(input_stream):
    """
    Accepts a stream of CSV and yields test_results data as tuples of the form:

        test_code, practice_code, month, result_category, count
    """
    reader = csv.reader(input_stream)
    headers = next(reader)
    try:
        test_code_col = headers.index("test_code")
        practice_col = headers.index("practice_code")
        date_col = headers.index("month")
        category_col = headers.index("result_category")
        count_col = headers.index("count")
    except ValueError as e:
        raise MissingHeaderError(str(e))
    for row in reader:
        yield (
            # These sometimes have trailing spaces in the CSV
            row[test_code_col].strip(),
            row[practice_col].strip(),
            # We only need the YYYY-MM-DD part of the date
            row[date_col][:10],
            int(row[category_col]),
            int(row[count_col]),
        )


def build_matrices(test_results, practices, dates):
    """Accepts an iterable of test_results (sorted by test), plus
    mappings of pratice codes and date strings to their respective
    row/column offsets. Yields tuples of the form:

        test_code, result_category, count_matrix

    Where the matrices contain the counts for that test_code and category for
    every practice and date.

    """
    max_row = max(practices.values())
    max_col = max(dates.values())
    shape = (max_row + 1, max_col + 1)
    # requires input to be sorted by test code for each month
    grouped_by_test_code = groupby(test_results, lambda row: row[0])
    for test_code, row_group in grouped_by_test_code:
        counts_matrix = sparse_matrix(shape, integer=True)
        for _, practice, date, category, count in row_group:
            practice_offset = practices[practice]
            date_offset = dates[date]
            counts_matrix[practice_offset, date_offset] = count
        yield MatrixRow(test_code, category, finalise_matrix(counts_matrix))


def format_as_sql_rows(matrices, connection):
    """
    Given an iterable of MatrixRows (which contain a test code plus all
    count data for that test) yield tuples of values ready for
    insertion into SQLite
    """
    cursor = connection.cursor()
    num_tests = next(cursor.execute("SELECT COUNT(*) FROM tests"))[0]
    count = 0
    for row in matrices:
        count += 1
        # We make sure we have a row for every test code + category in the data, even ones
        # we didn't know about previously. This is a hack that we won't need
        # once we can use SQLite v3.24.0 which has proper UPSERT support.
        for category in range(
            constants.MIN_RESULT_CATEGORY, constants.MAX_RESULT_CATEGORY + 1
        ):
            cursor.execute(
                "INSERT OR IGNORE INTO tests (test_code, result_category) VALUES (?, ?)",
                [row.test_code, category],
            )
        if should_log_message(count):
            logger.info("Writing data for %s (%s/%s)", row.test_code, count, num_tests)
        yield (
            sqlite3.Binary(serialize_compressed(row.count)),
            row.test_code,
            row.result_category,
        )
    logger.info("Finished writing data for %s tests", count)


def should_log_message(n):
    """
    To avoid cluttering log output we don't log the insertion of every single
    presentation
    """
    if n <= 10:
        return True
    if n == 100:
        return True
    return n % 200 == 0
