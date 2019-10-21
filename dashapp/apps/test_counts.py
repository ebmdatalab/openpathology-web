import logging

import plotly.graph_objs as go
from dash.dependencies import Input, Output

from app import app
from apps.base import get_sorted_group_keys
from data import get_count_data
from data import get_test_list
from stateful_routing import get_state
import settings


logger = logging.getLogger(__name__)


@app.callback(Output("counts-graph", "figure"), [Input("page-state", "children")])
def update_counts(page_state):
    page_state = get_state(page_state)
    if page_state.get("page_id") != settings.COUNTS_CHART_ID:
        return {}

    numerators = page_state.get("numerators", [])
    denominators = page_state.get("denominators", [])
    result_filter = page_state.get("result_filter", [])
    groupby = page_state.get("groupby", None)
    practice_filter_entity = page_state.get("practice_filter_entity", None)
    entity_ids_for_practice_filter = page_state.get(
        "entity_ids_for_practice_filter", []
    )

    if groupby == "practice":
        col_name = "practice_id"
    else:
        col_name = groupby
    df = get_count_data(
        numerators=numerators,
        denominators=denominators,
        by=col_name,
        practice_filter_entity=practice_filter_entity,
        entity_ids_for_practice_filter=entity_ids_for_practice_filter,
        result_filter=result_filter,
    )
    traces = []
    for entity_id in get_sorted_group_keys(df, col_name):
        if col_name == "result_category":
            label = settings.ERROR_CODES[entity_id]
        else:
            label = entity_id
        trace_df = df[df[col_name] == entity_id]
        trace_df["label"] = (
            trace_df["numerator"].astype(str)
            + " "
            + label
            + " per "
            + trace_df["denominator"].astype(str)
            + " patients"
        )
        traces.append(
            go.Scatter(
                x=trace_df["month"],
                y=trace_df["calc_value"],
                text=trace_df["label"],
                hoverinfo="text",
                showlegend=True,
            )
        )
    return {"data": traces}


@app.callback(Output("counts-table", "data"), [Input("page-state", "children")])
def update_counts_table(page_state):
    page_state = get_state(page_state)
    if page_state.get("page_id") != settings.COUNTS_CHART_ID:
        return {}

    numerators = page_state.get("numerators", [])
    denominators = page_state.get("denominators", [])
    result_filter = page_state.get("result_filter", [])
    groupby = page_state.get("groupby", None)
    practice_filter_entity = page_state.get("practice_filter_entity", None)
    entity_ids_for_practice_filter = page_state.get(
        "entity_ids_for_practice_filter", []
    )

    if groupby == "practice":
        col_name = "practice_id"
    else:
        col_name = groupby
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
    # XXX possibly remove this
    df["month"] = df["month"].dt.strftime("%Y-%m-%d")
    df["result_category"] = df["result_category"].replace(settings.ERROR_CODES)
    return df.to_dict("records")
