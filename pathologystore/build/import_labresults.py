import csv
from itertools import groupby
import logging
import os.path
import sqlite3

from matrixstore.matrix_ops import sparse_matrix, finalise_matrix
from matrixstore.serializer import serialize_compressed
from common.constants import RESULT_CATEGORIES


logger = logging.getLogger(__name__)


class MissingHeaderError(Exception):
    pass


def import_labresults(input_csv_file, sqlite_path):
    if not os.path.exists(sqlite_path):
        raise RuntimeError("No SQLite file at: {}".format(sqlite_path))
    connection = sqlite3.connect(sqlite_path)
    # Trade crash-safety for insert speed
    connection.execute("PRAGMA synchronous=OFF")
    labresults = sorted(get_labresults(input_csv_file))
    write_labresults(connection, labresults)
    connection.commit()
    connection.close()


def get_labresults(input_csv_file):
    with open(input_csv_file) as f:
        reader = csv.reader(f)
        headers = next(reader)
        try:
            test_code_col = headers.index('test_code')
            practice_col = headers.index("source")
            date_col = headers.index("month")
            result_category_col = headers.index('result_category')
            count_col = headers.index('count')
        except ValueError as e:
            raise MissingHeaderError(str(e))
        for row in reader:
            yield (
                row[test_code_col],
                row[practice_col],
                row[date_col].replace('/', '-'),
                row[result_category_col],
                count_str_to_int(row[count_col])
            )


def count_str_to_int(count_str):
    if count_str == '1-5':
        return 1
    else:
        return int(count_str)


def write_labresults(connection, labresults):
    result_names = [name for (code, name, label) in RESULT_CATEGORIES]
    result_codes = [str(code) for (code, name, label) in RESULT_CATEGORIES]
    result_codes = {code: i for (i, code) in enumerate(result_codes)}
    cursor = connection.cursor()
    # Map practice codes and date strings to their corresponding row/column
    # offset in the matrix
    practices = dict(cursor.execute("SELECT code, offset FROM practice"))
    dates = dict(cursor.execute("SELECT date, offset FROM date"))
    matrices = build_matrices(labresults, practices, dates, result_codes)
    rows = format_as_sql_rows(matrices)
    columns = ['test_code'] + result_names
    cursor.executemany(
        """
        INSERT INTO labtest ({columns}) VALUES ({placeholders})
        """.format(
            columns=','.join(columns),
            placeholders=','.join('?' * len(columns))
        ),
        rows,
    )


def format_as_sql_rows(matrices):
    for test_code, matrix_values in matrices:
        row = [sqlite3.Binary(serialize_compressed(m)) for m in matrix_values]
        row.insert(0, test_code)
        yield row


def build_matrices(labresults, practices, dates, result_codes):
    unknown_practices = set()
    unknown_dates = set()
    max_row = max(practices.values())
    max_col = max(dates.values())
    shape = (max_row + 1, max_col + 1)
    grouped_by_test_code = groupby(labresults, lambda row: row[0])
    for test_code, row_group in grouped_by_test_code:
        row_matrices = [
            sparse_matrix(shape, integer=False) for _ in result_codes
        ]
        for _, practice, date, result_code, count in row_group:
            try:
                practice_offset = practices[practice]
            except KeyError:
                if practice not in unknown_practices:
                    unknown_practices.add(practice)
                    logger.info('Skipping unknown practice: %s', practice)
                continue
            try:
                date_offset = dates[date]
            except KeyError:
                if date not in unknown_dates:
                    unknown_dates.add(date)
                    logger.info('Skipping out-of-range date: %s', date)
                continue
            index = (practice_offset, date_offset)
            result_matrix_index = result_codes[result_code]
            result_matrix = row_matrices[result_matrix_index]
            result_matrix[index] = count
        row_matrices = map(finalise_matrix, row_matrices)
        yield test_code, row_matrices


