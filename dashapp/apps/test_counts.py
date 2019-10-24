import logging

import plotly.graph_objs as go
from dash.dependencies import Input, Output

from app import app
from apps.base import get_sorted_group_keys
from apps.base import get_chart_title

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
    title = get_chart_title(numerators, denominators, result_filter, col_name)
    for entity_id in get_sorted_group_keys(df, col_name):
        if col_name == "result_category":
            label = settings.ERROR_CODES[entity_id]
        else:
            label = entity_id
        trace_df = df[df[col_name] == entity_id]
        traces.append(
            go.Scatter(
                x=trace_df["month"],
                y=trace_df["calc_value"],
                name=label,
                text=trace_df["label"],
                hoverinfo="text",
                showlegend=True,
            )
        )
    return {"data": traces, "layout": go.Layout(title=title)}
