import pandas as pd
from app import cache

import settings


@cache.memoize()
def get_data(sample_size=None):
    """Get suitably massaged data
    """
    df = pd.read_csv(settings.CSV_DIR / "test_data.csv.zip")

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


def get_count_data(
    numerators=[],
    denominators=[],
    result_filter=None,
    practice_filter_entity=None,
    entity_ids_for_practice_filter=[],
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
        cols = ["month", "total_list_size", "practice_id", "ccg_id", "count", "error"]
        groupby = ["month", "practice_id", "ccg_id"]
        required_cols = [
            "month",
            "total_list_size",
            "practice_id",
            "calc_value",
            "calc_value_error",
            "ccg_id",
        ]
    # XXX how do we do this.
    # We group by X, then do calc-value; but what about the percentiles?
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

    base_and_query = []
    if practice_filter_entity and "all" not in entity_ids_for_practice_filter:
        base_and_query.append(
            f"({practice_filter_entity}.isin({entity_ids_for_practice_filter}))"
        )
    numerator_and_query = base_and_query[:]
    if result_filter:
        assert result_filter in [
            "within_range",
            "under_range",
            "over_range",
            "error",
            "all",
        ]
        if result_filter == "within_range":
            numerator_and_query.append(f"(result_category == {settings.WITHIN_RANGE})")
        elif result_filter == "under_range":
            numerator_and_query.append(f"(result_category == {settings.UNDER_RANGE})")
        elif result_filter == "over_range":
            numerator_and_query.append(f"(result_category == {settings.OVER_RANGE})")
        elif result_filter == "error":
            numerator_and_query.append("(result_category > 1)")
    if numerators and numerators != ["all"]:
        numerator_and_query += [f"(test_code.isin({numerators}))"]
    if numerator_and_query:
        filtered_df = df.query(" & ".join(numerator_and_query))
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
        denominator_and_query = base_and_query[:]
        denominator_and_query += [f"test_code.isin({denominators})"]
        filtered_df = df.query(" & ".join(denominator_and_query))
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
    # The fillname is to work around this bug: https://github.com/plotly/plotly.js/issues/3296
    return num_df_agg[required_cols].sort_values("month").fillna(0)


@cache.memoize()
def get_test_list():
    return pd.read_csv(settings.CSV_DIR / "test_codes.csv")


@cache.memoize()
def get_ccg_list():
    """Get suitably massaged data
    """
    return [{"value": x, "label": x} for x in get_data().ccg_id.unique()]


def get_measures():
    return pd.read_csv(settings.CSV_DIR / "measures.csv")
