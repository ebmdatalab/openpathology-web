from unittest.mock import patch
import pandas as pd
from data import get_count_data


def make_df():
    data = [
        ["2018-01-01", 1, "FBC", 0, 10, 0, 40],
        ["2018-01-01", 1, "FBC", -1, 10, 0, 40],
        ["2018-01-01", 1, "HB1", 2, 20, 0, 40],
        ["2018-01-01", 2, "FBC", 0, 10, 0, 60],
        ["2018-01-01", 2, "FBC", 0, 10, 0, 60],
        ["2018-01-01", 2, "HB1", 2, 10, 0, 60],
    ]
    return pd.DataFrame(
        data,
        columns=[
            "month",
            "practice_id",
            "test_code",
            "result_category",
            "count",
            "error",
            "total_list_size",
        ],
    )


@patch("data.get_data")
def test_count_data_no_filter(mock_get_data):
    mock_get_data.return_value = make_df()
    result = get_count_data(["FBC"], ["per1000"])
    assert result[result["practice_id"] == 1]["calc_value"].iloc[0] == 500


@patch("data.get_data")
def test_count_data_no_filter_all_test_denom(mock_get_data):
    mock_get_data.return_value = make_df()
    result = get_count_data(["FBC"], ["FBC", "HB1"])
    assert result[result["practice_id"] == 1]["calc_value"].iloc[0] == 0.5


@patch("data.get_data")
def test_count_data_only_within(mock_get_data):
    mock_get_data.return_value = make_df()
    result = get_count_data(["FBC"], ["per1000"], result_filter="within_range")
    assert result[result["practice_id"] == 1]["calc_value"].iloc[0] == 250
