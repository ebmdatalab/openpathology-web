import pandas as pd
from app import cache

import settings


@cache.memoize()
def get_data(sample_size=None):
    """Get suitably massaged data
    """
    df = pd.read_csv(settings.CSV_DIR / "all_processed.csv")

    # Convert month to datetime
    df.loc[:, "month"] = pd.to_datetime(df["month"])

    if sample_size:
        some_practices = df.practice_id.sample(sample_size)
        return df[df.loc[:, "practice_id"].isin(some_practices)]
    else:
        return df


@cache.memoize()
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
    """
    df = get_data(sample_size)
    if by == "practice_id":
        cols = ["month", "total_list_size", "practice_id", "ccg_id", "count", "error"]
        groupby = ["month", "practice_id", "ccg_id"]
        required_cols = [
            "month",
            "total_list_size",
            "practice_id",
            "numerator",
            "denominator",
            "label",
            "calc_value",
            "calc_value_error",
            "ccg_id",
        ]
    # XXX how do we do this.
    # We group by X, then do calc-value; but what about the percentiles?
    elif by == "test_code":
        cols = ["month", "test_code", "count", "error", "total_list_size"]
        groupby = ["month", "test_code"]
        required_cols = [
            "month",
            "test_code",
            "calc_value",
            "calc_value_error",
            "label",
            "numerator",
            "denominator",
        ]
    elif by == "result_category":
        cols = ["month", "result_category", "count", "error", "total_list_size"]
        groupby = ["month", "result_category"]
        required_cols = [
            "month",
            "result_category",
            "calc_value",
            "calc_value_error",
            "label",
            "numerator",
            "denominator",
        ]
    elif by == "ccg_id":
        cols = ["month", "total_list_size", "ccg_id", "count", "error"]
        groupby = ["month", "ccg_id"]
        required_cols = [
            "month",
            "total_list_size",
            "label",
            "numerator",
            "denominator",
            "ccg_id",
            "calc_value",
            "calc_value_error",
        ]
    elif not by:
        cols = [
            "month",
            "test_code",
            "result_category",
            "calc_value",
            "calc_value_error",
            "practice_id",
            "ccg_id",
            "total_list_size",
        ]
        required_cols = cols + [
            "label",
            "numerator",
            "numerator_error",
            "denominator",
            "denominator_error",
        ]

        groupby = None
    base_and_query = []
    if practice_filter_entity and "all" not in entity_ids_for_practice_filter:
        base_and_query.append(
            f"({practice_filter_entity}.isin({entity_ids_for_practice_filter}))"
        )
    numerator_and_query = base_and_query[:]
    if result_filter:
        if result_filter == "within_range":
            numerator_and_query.append(f"(result_category == {settings.WITHIN_RANGE})")
        elif result_filter == "under_range":
            numerator_and_query.append(f"(result_category == {settings.UNDER_RANGE})")
        elif result_filter == "over_range":
            numerator_and_query.append(f"(result_category == {settings.OVER_RANGE})")
        elif result_filter == "error":
            numerator_and_query.append("(result_category > 1)")
        elif str(result_filter).isnumeric():
            numerator_and_query.append(f"(result_category == {result_filter})")

    if numerators and numerators != ["all"]:
        numerator_and_query += [f"(test_code.isin({numerators}))"]
    if numerator_and_query:
        filtered_df = df.query(" & ".join(numerator_and_query))
    else:
        filtered_df = df
    if groupby:
        num_df_agg = filtered_df[cols].groupby(groupby).sum().reset_index()
    else:
        num_df_agg = filtered_df
    if denominators == ["per1000"]:
        num_df_agg.loc[:, "denominator"] = num_df_agg["total_list_size"]
        num_df_agg.loc[:, "denominator_error"] = num_df_agg["error"]
        num_df_agg.loc[:, "calc_value"] = (
            num_df_agg["count"] / num_df_agg["total_list_size"] * 1000
        )
        num_df_agg.loc[:, "calc_value_error"] = (
            num_df_agg["error"] / num_df_agg["total_list_size"] * 1000
        )
    elif not denominators or denominators == ["raw"]:
        num_df_agg.loc[:, "denominator"] = num_df_agg["count"]
        num_df_agg.loc[:, "denominator_error"] = num_df_agg["error"]
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
        num_df_agg = num_df_agg.rename(
            columns={"count_denom": "denominator", "error_denom": "denominator_error"}
        )
    num_df_agg = num_df_agg.rename(
        columns={"count": "numerator", "error": "numerator_error"}
    )
    num_df_agg["label"] = (
        num_df_agg["numerator"].astype(str)
        + " "
        + " + ".join(numerators)
        + " per "
        + num_df_agg["denominator"].astype(str)
        + " patients"
    )

    # The fillname is to work around this bug: https://github.com/plotly/plotly.js/issues/3296
    return num_df_agg[required_cols].sort_values("month").fillna(0)


def get_test_list():
    """Get a list of tests suitable for showing in HTML dropdown forms
    """
    df = pd.read_csv(settings.CSV_DIR / "test_codes.csv")
    df = df[["datalab_testcode", "testname"]]
    df = df.rename(columns={"datalab_testcode": "value", "testname": "label"})
    return df


@cache.memoize()
def get_ccg_list():
    """Get suitably massaged data
    """
    return [{"value": x, "label": x} for x in get_data().ccg_id.unique()]


def get_measures():
    return pd.read_csv(settings.CSV_DIR / "measures.csv")
