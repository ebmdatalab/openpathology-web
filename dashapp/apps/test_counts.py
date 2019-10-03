import logging

import plotly.graph_objs as go
from dash.dependencies import Input, Output

from app import app
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
    test_codes = page_state.get("test_codes", list(get_test_list().datalab_testcode))
    denominator = page_state.get("denominator", None)
    df = get_count_data(numerator=test_codes, denominator=denominator, by="test_code")
    traces = []

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
