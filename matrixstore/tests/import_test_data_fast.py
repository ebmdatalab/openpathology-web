import csv

from matrixstore.build.init_db import SCHEMA_SQL, generate_dates, import_dates
from matrixstore.build.import_practice_stats import (
    write_practice_stats,
    parse_practice_statistics_csv,
)
from matrixstore.build.import_test_results import (
    delete_tests_with_no_results,
    write_test_results,
    parse_test_results_csv,
)


from common import constants


def import_test_data_fast(sqlite_conn, data_factory, end_date, months=None):
    """
    Imports the data in `data_factory` into the supplied SQLite connection
    without touching any external services such as BigQuery or Google Cloud
    Storage (and indeed without touching disk, if the SQLite database is in
    memory).
    """
    dates = generate_dates(end_date, months=months)

    # Disable the sqlite module's magical transaction handling features because
    # we want to use our own transactions below
    previous_isolation_level = sqlite_conn.isolation_level
    sqlite_conn.isolation_level = None

    init_db(sqlite_conn, data_factory, dates)
    import_practice_stats(sqlite_conn, data_factory, dates)
    import_test_results(sqlite_conn, data_factory, dates)
    delete_tests_with_no_results(sqlite_conn)
    sqlite_conn.isolation_level = previous_isolation_level
    sqlite_conn.commit()


def init_db(sqlite_conn, data_factory, dates):
    sqlite_conn.executescript(SCHEMA_SQL)
    import_dates(sqlite_conn, dates)
    practice_codes = _get_active_practice_codes(data_factory, dates)
    sqlite_conn.executemany(
        "INSERT INTO practice (offset, code) VALUES (?, ?)", enumerate(practice_codes)
    )
    categories = [x[0] for x in constants.RESULT_CATEGORIES]
    tests = []
    for result_category in categories:
        for p in data_factory.tests:
            tests.append((p["test_code"], result_category))

    sqlite_conn.executemany(
        """
        INSERT INTO tests
          (test_code, result_category)
          VALUES (?, ?)
        """,
        tests,
    )


def import_practice_stats(sqlite_conn, data_factory, dates):
    filtered_practice_stats = _filter_by_date(data_factory.practice_statistics, dates)
    practice_statistics_csv = _dicts_to_csv(filtered_practice_stats)
    practice_statistics = parse_practice_statistics_csv(practice_statistics_csv)
    write_practice_stats(sqlite_conn, practice_statistics)


def import_test_results(sqlite_conn, data_factory, dates):
    filtered_test_results = _filter_by_date(data_factory.test_results, dates)
    sorted_test_results = sorted(
        filtered_test_results,
        key=lambda p: (p["test_code"], p["practice_code"], p["month"]),
    )
    test_results_csv = _dicts_to_csv(sorted_test_results)
    test_results = parse_test_results_csv(test_results_csv)
    write_test_results(sqlite_conn, test_results)


def _get_active_practice_codes(data_factory, dates):
    practice_codes = set()
    for test_result in _filter_by_date(data_factory.test_results, dates):
        practice_codes.add(test_result["practice_code"])
    for practice_stat in _filter_by_date(data_factory.practice_statistics, dates):
        practice_codes.add(practice_stat["practice"])
    return sorted(practice_codes)


def _filter_by_date(items, dates):
    for item in items:
        if item["month"][:10] in dates:
            yield item


# `csv.writer` wants a file-like object to write its output to, but we just
# want to grab each line of output as it's written. Rather than mess around
# with StringIO we can just give it an ordinary list, but with its `append`
# method aliased to `write` and then we can pop the lines off after
# `csv.writer` has written them
class ListFile(list):
    write = list.append


def _dicts_to_csv(dicts):
    """
    Takes an interable of dictionaries (assumed to all have the same keys) and
    returns an iterable of strings in CSV format. The first line contains
    headers, which are the dictionary keys.
    """
    lines = ListFile()
    writer = None
    for dictionary in dicts:
        if not writer:
            fieldnames = dictionary.keys()
            writer = csv.DictWriter(lines, fieldnames)
            writer.writeheader()
            yield lines.pop()
        writer.writerow(dictionary)
        yield lines.pop()
