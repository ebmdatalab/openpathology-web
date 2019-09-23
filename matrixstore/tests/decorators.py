import json

from frontend.models import (
    Practice,
    PracticeStatistics,
    Prescription,
    Presentation,
    ImportLog,
)
from matrixstore.tests.matrixstore_factory import (
    matrixstore_from_data_factory,
    patch_global_matrixstore,
)


def copy_fixtures_to_matrixstore(cls):
    """
    Decorator for TestCase classes which copies data from Postgres into an
    in-memory MatrixStore instance. This allows us to re-use database fixtures,
    and the tests designed to work with those fixtures, to test
    MatrixStore-powered code.
    """
    # These methods have been decorated with `@classmethod` so we need to use
    # `__func__` to get a reference to the original, undecorated method
    decorated_setUpClass = cls.setUpClass.__func__
    decorated_tearDownClass = cls.tearDownClass.__func__

    def setUpClass(inner_cls):
        decorated_setUpClass(inner_cls)
        matrixstore = matrixstore_from_postgres()
        stop_patching = patch_global_matrixstore(matrixstore)
        # Have to wrap this in a staticmethod decorator otherwise Python thinks
        # we're trying to create a new class method
        inner_cls._stop_patching = staticmethod(stop_patching)

    def tearDownClass(inner_cls):
        inner_cls._stop_patching()
        decorated_tearDownClass(inner_cls)

    cls.setUpClass = classmethod(setUpClass)
    cls.tearDownClass = classmethod(tearDownClass)
    return cls


def matrixstore_from_postgres():
    """
    Creates a MatrixStore SQLite database using data sourced from Postgres.
    This provides an easy way of using existing test fixtures with the
    MatrixStore.
    """
    latest_date = ImportLog.objects.latest_in_category("prescribing").current_at
    end_date = str(latest_date)[:7]
    return matrixstore_from_data_factory(
        _DatabaseFixtures(), end_date=end_date, months=60
    )


class _DatabaseFixtures(object):
    """
    Presents the same attributes as a DataFactory instance but with data read
    from the database (where it was presumably loaded from test fixtures),
    rather than randomly generated.
    """

    def __init__(self):
        self.prescribing = [
            {
                "month": str(p.processing_date),
                "practice": p.practice_id,
                "bnf_code": p.presentation_code,
                "items": p.total_items,
                "quantity": int(p.quantity),
                # Net cost shouldn't really ever be null, but it is in some of
                # our old test fixtures
                "net_cost": p.net_cost or 0,
                "actual_cost": p.actual_cost,
                # We don't care about any of these fields, the MatrixStore
                # import doesn't use them
                "bnf_name": None,
                "sha": None,
                "pcn": None,
                "pct": None,
                "stp": None,
                "regional_team": None,
            }
            for p in Prescription.objects.all()
        ]
        self.presentations = [
            {
                "bnf_code": p.bnf_code,
                "name": p.name,
                "is_generic": p.is_generic,
                "adq_per_quantity": p.adq_per_quantity,
            }
            for p in Presentation.objects.all()
        ]
        self.practices = [
            {
                "code": p.code,
                "status_code": p.status_code,
                "name": p.name,
                # We don't currently care about any of these fields
                "address1": None,
                "address2": None,
                "address3": None,
                "address4": None,
                "address5": None,
                "postcode": None,
                "location": None,
                "ccg_id": None,
                "setting": None,
                "close_date": None,
                "join_provider_date": None,
                "leave_provider_date": None,
                "open_date": None,
            }
            for p in Practice.objects.all()
        ]
        self.practice_statistics = [
            {
                "month": str(ps.date),
                "practice": ps.practice_id,
                # The importer doesn't use this field
                "pct_id": None,
                "astro_pu_items": ps.astro_pu_items,
                "astro_pu_cost": ps.astro_pu_cost,
                "star_pu": json.dumps(ps.star_pu),
                "total_list_size": ps.total_list_size,
                "male_0_4": ps.male_0_4,
                "female_0_4": ps.female_0_4,
                "male_5_14": ps.male_5_14,
                "female_5_14": ps.female_5_14,
                "male_15_24": ps.male_15_24,
                "female_15_24": ps.female_15_24,
                "male_25_34": ps.male_25_34,
                "female_25_34": ps.female_25_34,
                "male_35_44": ps.male_35_44,
                "female_35_44": ps.female_35_44,
                "male_45_54": ps.male_45_54,
                "female_45_54": ps.female_45_54,
                "male_55_64": ps.male_55_64,
                "female_55_64": ps.female_55_64,
                "male_65_74": ps.male_65_74,
                "female_65_74": ps.female_65_74,
                "male_75_plus": ps.male_75_plus,
                "female_75_plus": ps.female_75_plus,
            }
            for ps in PracticeStatistics.objects.all()
        ]
        # We don't need to update old BNF codes in our test fixtures
        self.bnf_map = []
