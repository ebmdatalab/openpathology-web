import pandas as pd
from app import cache

import settings


@cache.memoize()
def get_data(sample_size=None):
    """Get suitably massaged data
    """
    df = pd.read_csv(settings.CSV_DIR / "cornwall_data_processed_anonymised.csv")

    # Convert month to datetime
    df.loc[:, "month"] = pd.to_datetime(df["month"])

    # estimate errors from data suppression
    df.loc[df["count"] == 3, "error"] = 2
    df["error"].fillna(0, inplace=True)

    # copy anonymised id into column named "practice_id"
    df = df.loc[pd.notnull(df["anon_id"])]
    df["practice_id"] = df["anon_id"].astype(str).str.replace(".0", "")

    if sample_size:
        some_practices = df.practice_id.sample(sample_size)
        return df[df.loc[:, "practice_id"].isin(some_practices)]
    else:
        return df


def _agg_count_data(df, by):
    return


def get_count_data(
    numerators=[],
    denominators=[],
    result_filter=None,
    by="practice_id",
    sample_size=None,
):
    """Get anonymised count data (for all categories) by month and test_code and practice

    numerators: an array of test codes
    denominators: an array of tests codes, or `per1000`, or None
    result_filter: ["within_range", "under_range", "over_range", "error"]
    """
    df = get_data(sample_size)
    if by == "practice_id":
        cols = ["month", "total_list_size", "practice_id", "count", "error"]
        groupby = ["month", "practice_id"]
        required_cols = [
            "month",
            "total_list_size",
            "practice_id",
            "calc_value",
            "calc_value_error",
        ]

    elif by == "test_code":
        cols = ["month", "test_code", "count", "error", "total_list_size"]
        groupby = ["month", "test_code"]
        required_cols = ["month", "test_code", "calc_value", "calc_value_error"]
    elif by == "ccg_id":
        cols = ["month", "total_list_size", "ccg_id", "count", "error"]
        groupby = ["month", "ccg_id"]
        required_cols = [
            "month",
            "total_list_size",
            "ccg_id",
            "calc_value",
            "calc_value_error",
        ]

    and_query = []
    if result_filter:
        assert result_filter in [
            "within_range",
            "under_range",
            "over_range",
            "error",
            "all",
        ]
        if result_filter == "within_range":
            and_query.append(f"(result_category == {settings.WITHIN_RANGE})")
        elif result_filter == "under_range":
            and_query.append(f"(result_category == {settings.UNDER_RANGE})")
        elif result_filter == "over_range":
            and_query.append(f"(result_category == {settings.OVER_RANGE})")
        elif result_filter == "error":
            and_query.append("(result_category > 1)")
    num_filter = and_query[:]
    if numerators and numerators != ["all"]:
        num_filter += [f"(test_code.isin({numerators}))"]
    if num_filter:
        filtered_df = df.query(" & ".join(num_filter))
    else:
        filtered_df = df
    num_df_agg = filtered_df[cols].groupby(groupby).sum().reset_index()
    if denominators == ["per1000"]:
        num_df_agg.loc[:, "calc_value"] = (
            num_df_agg["count"] / num_df_agg["total_list_size"] * 1000
        )
        num_df_agg.loc[:, "calc_value_error"] = (
            num_df_agg["error"] / num_df_agg["total_list_size"] * 1000
        )
    elif not denominators or denominators == ["raw"]:
        num_df_agg.loc[:, "calc_value"] = num_df_agg["count"]
        num_df_agg.loc[:, "calc_value_error"] = num_df_agg["error"]

    else:
        # denominator is list of tests
        if by == "test_code":
            # The denominator needs to be summed across all tests
            groupby = ["month"]
        filtered_df = df.query(f"test_code.isin({denominators})")
        denom_df_agg = filtered_df[cols].groupby(groupby).sum().reset_index()
        num_df_agg = num_df_agg.merge(
            denom_df_agg,
            how="right",
            left_on=groupby,
            right_on=groupby,
            suffixes=("", "_denom"),
        )
        num_df_agg.loc[:, "calc_value"] = (
            num_df_agg["count"] / num_df_agg["count_denom"]
        )
        num_df_agg.loc[:, "calc_value_error"] = (
            num_df_agg["error"] / num_df_agg["error_denom"]
        )
    return num_df_agg[required_cols]


@cache.memoize()
def get_test_list():
    return pd.read_csv(settings.CSV_DIR / "test_codes.csv")
