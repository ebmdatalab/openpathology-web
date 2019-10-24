import logging
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output

import numpy as np
from app import app
from apps.base import get_sorted_group_keys
from apps.base import get_chart_title
from data import get_count_data
from stateful_routing import get_state
import settings


logger = logging.getLogger(__name__)


def get_practice_deciles(df):
    """Compute deciles across `calc_value` over `practice_id` for each month.

    Returns a list of (decile, value) tuples (e.g. (10, 4.223))
    """
    deciles = np.array(range(10, 100, 10))
    vals_by_practice = df.pivot(columns="month", values="calc_value")
    deciles_data = np.nanpercentile(vals_by_practice, axis=0, q=deciles)
    return zip(deciles, deciles_data)


def get_practice_decile_traces(df):
    """Return a set of `Scatter` traces  suitable for adding to a Dash figure
    """
    deciles_traces = []
    months = pd.to_datetime(df["month"].unique())
    for n, decile in get_practice_deciles(df):
        if n == 50:
            style = "dash"
        else:
            style = "dot"
        deciles_traces.append(
            go.Scatter(
                x=months,
                y=decile,
                name="{}th".format(n),
                line=dict(color="blue", width=1, dash=style),
                hoverinfo="skip",
            )
        )
    return deciles_traces


@app.callback(
    Output("deciles-container", "children"), [Input("page-state", "children")]
)
def update_deciles(page_state):
    page_state = get_state(page_state)
    if page_state.get("page_id") != settings.DECILES_CHART_ID:
        return html.Div()

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

    trace_df = get_count_data(
        numerators=numerators,
        denominators=denominators,
        result_filter=result_filter,
        practice_filter_entity=practice_filter_entity,
        entity_ids_for_practice_filter=entity_ids_for_practice_filter,
        by=col_name,
    )
    traces = []
    deciles_traces = get_practice_decile_traces(trace_df)
    if not deciles_traces:
        return html.Div()
    months = deciles_traces[0].x
    ymax = trace_df.calc_value.max() + trace_df.calc_value_error.max()
    if (
        col_name in ["practice_id", "ccg_id"]
        and "all" not in entity_ids_for_practice_filter
    ):
        entity_ids = get_sorted_group_keys(
            trace_df[trace_df.ccg_id.isin(entity_ids_for_practice_filter)], col_name
        )
    else:
        entity_ids = get_sorted_group_keys(trace_df, col_name)
    limit = 80  # XXX this is cos we can't draw so many charts without breaking
    # the browser. Ideally we'd fix this with load-on-scroll

    # Create a graph for each practice
    graphs = []
    for entity_id in entity_ids[:limit]:
        entity_df = trace_df[trace_df[col_name] == entity_id]
        traces = []
        # First, plot the practice line
        traces.append(
            go.Scatter(
                x=entity_df["month"],
                y=entity_df["calc_value"],
                text=trace_df["label"],
                hoverinfo="text",
                name=str(entity_id),
                line=dict(color="red", width=1, dash="solid"),
            )
        )
        if entity_df["calc_value_error"].sum() > 0:
            # If there's any error, bounds and fill
            traces.append(
                go.Scatter(
                    x=entity_df["month"],
                    y=entity_df["calc_value"] + entity_df["calc_value_error"],
                    name=str(entity_id),
                    line=dict(color="red", width=1, dash="dot"),
                    hoverinfo="skip",
                )
            )
            traces.append(
                go.Scatter(
                    x=entity_df["month"],
                    y=entity_df["calc_value"] - entity_df["calc_value_error"],
                    name=str(entity_id),
                    fill="tonexty",
                    line=dict(color="red", width=1, dash="dot"),
                    hoverinfo="skip",
                )
            )

        # Add the deciles
        traces.extend(deciles_traces)

        title = get_chart_title(numerators, denominators, result_filter, entity_id)
        # Add the traces to per-practice graph
        graph = dcc.Graph(
            id="graph-{}".format(entity_id),
            figure={
                "data": traces,
                "layout": go.Layout(
                    title=title,
                    yaxis={"range": [0, ymax]},
                    xaxis={"range": [months[0], months[-1]]},
                    showlegend=False,
                ),
            },
            config={"staticPlot": False},  # < -- XXX about twice as fast
        )
        graphs.append(graph)
    return html.Div(graphs)
