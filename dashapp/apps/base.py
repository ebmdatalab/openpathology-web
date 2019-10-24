"""Callbacks that apply to all pages
"""
from dash.dependencies import Input, Output

from app import app
from stateful_routing import get_state
from data import get_count_data
import settings


# for each chart, generate a function to show only that chart
def _create_show_chart_func(chart):
    """creates a callback function"""

    def show_chart(page_state):
        page_state = get_state(page_state)
        if page_state.get("page_id") == chart:
            return {"display": "block"}
        else:
            return {"display": "none"}

    return show_chart


# Register callbacks such that when the page state changes, only the
# page id currently indicated in the page state is shown
for chart in settings.CHARTS:
    app.callback(
        Output("{}-container".format(chart), "style"), [Input("page-state", "children")]
    )(_create_show_chart_func(chart))


def get_sorted_group_keys(df, group_by):
    """Compute a sort order for the practice charts, based on the mean
    calc_value of the last 6 months"""
    df2 = df.pivot_table(index=group_by, columns="month", values="calc_value")
    entity_ids = df2.reindex(
        df2.fillna(0).iloc[:, -6:].mean(axis=1).sort_values(ascending=False).index,
        axis=0,
    ).index
    return entity_ids


@app.callback(
    Output("counts-table-container", "style"), [Input("datatable-toggle", "value")]
)
def toggle_counts_table_visibility(toggle_state):
    if toggle_state:
        return {"display": "block"}
    else:
        return {"display": "none"}


@app.callback(
    Output("counts-table", "data"),
    [Input("page-state", "children"), Input("datatable-toggle", "value")],
)
def update_counts_table(page_state, toggle_state):
    page_state = get_state(page_state)
    if not toggle_state:
        return []

    numerators = page_state.get("numerators", [])
    denominators = page_state.get("denominators", [])
    result_filter = page_state.get("result_filter", [])
    practice_filter_entity = page_state.get("practice_filter_entity", None)
    entity_ids_for_practice_filter = page_state.get(
        "entity_ids_for_practice_filter", []
    )

    # XXX should page with python here
    # See https://dash.plot.ly/datatable/callbacks
    df = get_count_data(
        numerators=numerators,
        denominators=denominators,
        by=None,
        practice_filter_entity=practice_filter_entity,
        entity_ids_for_practice_filter=entity_ids_for_practice_filter,
        result_filter=result_filter,
    )
    # XXX make downloadable:
    # https://github.com/plotly/dash-core-components/issues/216 -
    # perhaps
    # https://community.plot.ly/t/allowing-users-to-download-csv-on-click/5550/9
    # XXX possibly remove this
    df["month"] = df["month"].dt.strftime("%Y-%m-%d")
    df["result_category"] = df["result_category"].replace(settings.ERROR_CODES)
    return df.to_dict("records")


def get_chart_title(numerators, denominators, result_filter, entity_id):

    # Make a title

    if not numerators or "all" in numerators:
        numerators_text = "all tests"
    else:
        numerators_text = " + ".join(numerators)
    if not denominators:
        denominators_text = "(raw numbers)"
    elif denominators == ["per1000"]:
        denominators_text = "per 1000 patients"
    else:
        denominators_text = "as a proportion of " + " + ".join(denominators)
    if result_filter and result_filter != "all":
        try:
            filter_text = (
                ", only showing results " + settings.ERROR_CODES[int(result_filter)]
            )
        except ValueError:
            filter_text = ", only showing results " + result_filter

    else:
        filter_text = ""

    title = "Count of {} {} for {}{}".format(
        numerators_text, denominators_text, entity_id, filter_text
    )
    return title
