from __future__ import division

import itertools
import json
import random
from common import constants
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_date


class DataFactory(object):
    """
    This class provides methods to generate test fixtures for the MatrixStore
    """

    def __init__(self, seed=36):
        self.random = random.Random()
        self.random.seed(seed)
        counter = itertools.count()
        self.next_id = lambda: next(counter)
        self.months = []
        self.practices = []
        self.practice_statistics = []
        self.tests = []
        self.test_results = []

    def create_months(self, start_date, num_months):
        date = parse_date(start_date)
        months = [
            (date + relativedelta(months=i)).strftime("%Y-%m-%d 00:00:00 UTC")
            for i in range(0, num_months)
        ]
        self.months = sorted(set(self.months + months))
        return months

    def create_practice(self):
        practice = {"code": "ABC{:03}".format(self.next_id())}
        self.practices.append(practice)
        return practice

    def create_practices(self, num_practices):
        return [self.create_practice() for i in range(num_practices)]

    def create_statistics_for_one_practice_and_month(self, practice, month):
        data = {
            "month": month,
            "practice": practice["code"],
            # We don't care about the PCT at the moment
            # We increment this value below
            "total_list_size": 0,
        }
        age_bands = (
            "0_4",
            "5_14",
            "15_24",
            "25_34",
            "35_44",
            "45_54",
            "55_64",
            "65_74",
            "75_plus",
        )
        for age_band in age_bands:
            for sex in ("male", "female"):
                value = self.random.randint(0, 1000)
                data["{}_{}".format(sex, age_band)] = value
                data["total_list_size"] += value
        self.practice_statistics.append(data)
        return data

    def create_practice_statistics(self, practices, months):
        return [
            self.create_statistics_for_one_practice_and_month(practice, month)
            for practice in practices
            for month in months
        ]

    def create_test(self):
        index = self.next_id()
        test = {"test_code": self.create_test_code(index)}
        self.tests.append(test)
        return test

    def create_test_code(self, index):
        return "TEST{}".format(index)

    def create_tests(self, num_tests):
        return [self.create_test() for i in range(num_tests)]

    def create_test_result(self, test, practice, month):
        """Create a set of test results for a random selection of possible result categories
        """
        categories = [x[0] for x in constants.RESULT_CATEGORIES]
        n = self.random.randint(1, len(categories))
        result_categories = self.random.sample(
            range(min(categories), max(categories) + 1), n
        )
        test_results = []
        for result_category in result_categories:
            test_result = {
                "month": month,
                "practice_code": practice["code"],
                "test_code": test["test_code"],
                "result_category": result_category,
                "count": self.random.randint(1, 100),
            }
            self.test_results.append(test_result)
            test_results.append(test_result)
        return test_results

    def create_test_results(self, tests, practices, months):
        test_results = []
        for practice in practices:
            # Make sure each practice tests in at least one month, although
            # probably not every month
            n = self.random.randint(1, len(months))
            selected_months = self.random.sample(months, n)
            for month in selected_months:
                # Make sure the practice requests at least one test,
                # although probably not every one
                n = self.random.randint(1, len(tests))
                selected_tests = self.random.sample(tests, n)
                for test in selected_tests:

                    test_results.append(self.create_test_result(test, practice, month))
        return test_results

    def create_all(
        self, start_date="2018-10-01", num_months=1, num_practices=1, num_tests=1
    ):
        months = self.create_months(start_date, num_months)
        practices = self.create_practices(num_practices)
        tests = self.create_tests(num_tests)
        self.create_practice_statistics(practices, months)
        self.create_test_results(tests, practices, months)
