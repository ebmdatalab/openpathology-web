from pathlib import Path

# Error/success codes for `result_category` field
WITHIN_RANGE = 0
UNDER_RANGE = -1
OVER_RANGE = 1
ERR_NO_REF_RANGE = 2
ERR_UNPARSEABLE_RESULT = 3
ERR_INVALID_SEX = 4
ERR_INVALID_RANGE_WITH_DIRECTION = 5
ERR_DISCARDED_AGE = 6
ERR_INVALID_REF_RANGE = 7
ERR_NO_TEST_CODE = 8


# A list of all the charts that appear in the app
HEATMAP_CHART_ID = "heatmap"
DECILES_CHART_ID = "deciles"
COUNTS_CHART_ID = "counts"
CHARTS = [HEATMAP_CHART_ID, DECILES_CHART_ID, COUNTS_CHART_ID, "measures"]

CSV_DIR = Path(__file__).parents[0] / "data_csvs"

CACHE_CONFIG = {
    # Use Redis in production?
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": "/tmp/",
}


ERROR_CODES = {
    0: "within range",
    -1: "under range",
    1: "over range",
    2: "with no ref range available",
    3: "with non-numeric result",
    4: "with invalid sex",
    5: "with no ref range calculated - impossible direction",
    6: "with no ref range calculated for children",
    7: "with no ref range calculated - invalid ref range",
}
