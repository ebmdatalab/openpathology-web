import logging

import plotly.graph_objs as go
from dash.dependencies import Input, Output

from app import app
from app import get_count_data
from stateful_routing import get_state
import settings


logger = logging.getLogger(__name__)


@app.callback(Output("counts-graph", "figure"), [Input("page-state", "children")])
def update_counts(page_state):
    page_state = get_state(page_state)
    if page_state.get("page_id") != settings.COUNTS_CHART_ID:
        return {}
    df = get_count_data()
    traces = []
    sample_practice = df.practice_id.sample(1).iloc[0]
    practice_id = page_state.get("practice_id", sample_practice) or sample_practice
    df = df[df["practice_id"] == int(practice_id)]
    test_codes = page_state.get("test_codes", []) or ["FBC"]

    for test_code in test_codes:
        trace_df = df[df.test_code == test_code]
        traces.append(
            go.Scatter(
                x=trace_df["month"],
                y=trace_df["calc_value"],
                name=test_code,
                showlegend=True,
            )
        )
    return {"data": traces}


@app.callback(Output("test-selector-table", "data"), [Input("page-state", "children")])
def update_table_selector(page_state):
    df = get_count_data()

    test_summary = (
        df.groupby("test_code")["count"]
        .sum()
        .reset_index()
        .sort_values("count", ascending=False)
    )
    test_summary.loc[:, "id"] = test_summary["test_code"]
    return test_summary.to_dict("records")
