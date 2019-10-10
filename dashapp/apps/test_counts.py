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
    entity_type = page_state.get("entity_type", None)
    if entity_type == "practice":
        col_name = "practice_id"
    elif entity_type == "test_code":
        col_name = entity_type
    df = get_count_data(
        numerators=numerators,
        denominators=denominators,
        by=col_name,
        result_filter=result_filter,
    )
    traces = []

    for entity_id in get_sorted_group_keys(df, col_name):
        trace_df = df[df[col_name] == entity_id]
        traces.append(
            go.Scatter(
                x=trace_df["month"],
                y=trace_df["calc_value"],
                name=entity_id,
                showlegend=True,
            )
        )
    return {"data": traces}
