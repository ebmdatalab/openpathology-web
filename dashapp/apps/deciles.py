import logging
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output

import numpy as np
from app import app
from data import get_count_data
from stateful_routing import get_state
import settings


logger = logging.getLogger(__name__)


def get_practice_deciles(df):
    """Compute deciles across `calc_value` over `practice_id` for each month.

    Returns a list of (decile, value) tuples (e.g. (10, 4.223))
    """
    deciles = np.array(range(10, 100, 10))
    vals_by_practice = df.pivot(
        index="practice_id", columns="month", values="calc_value"
    )
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


def get_sorted_practice_ids(df):
    """Compute a sort order for the practice charts, based on the mean
    calc_value of the last 6 months"""
    df2 = df.pivot(index="practice_id", columns="month", values="calc_value")
    practice_ids = df2.reindex(
        df2.fillna(0).iloc[:, -6:].mean(axis=1).sort_values(ascending=False).index,
        axis=0,
    ).index
    return practice_ids


@app.callback(
    Output("deciles-container", "children"), [Input("page-state", "children")]
)
def update_deciles(page_state):
    page_state = get_state(page_state)
    if page_state.get("page_id") != settings.DECILES_CHART_ID:
        return html.Div()

    practice_id = page_state.get("practice_id", None)
    test_codes = page_state.get("test_codes", None)
    if not test_codes:
        test_codes = ["FBC"]
    trace_df = get_count_data(numerator=test_codes, denominator="per1000")
    traces = []
    deciles_traces = get_practice_decile_traces(trace_df)
    months = deciles_traces[0].x
    ymax = trace_df.calc_value.max()
    if practice_id:
        practice_ids = [int(practice_id)]
    else:
        practice_ids = get_sorted_practice_ids(trace_df)

    # Create a graph for each practice
    graphs = []
    for practice_id in practice_ids:

        prac_df = trace_df[trace_df["practice_id"] == practice_id]
        traces = []
        # First, plot the practice line
        traces.append(
            go.Scatter(
                x=prac_df["month"],
                y=prac_df["calc_value"] + prac_df["calc_value_error"],
                name=str(practice_id),
                line=dict(color="red", width=1, dash="solid"),
            )
        )
        if prac_df["calc_value_error"].sum() > 0:
            # If there's any error, draw a bottom bound and fill
            traces.append(
                go.Scatter(
                    x=prac_df["month"],
                    y=prac_df["calc_value"] - prac_df["calc_value_error"],
                    name=str(practice_id),
                    line=dict(color="red", width=1, dash="solid"),
                    fill="tonexty",
                    hoverinfo="skip",
                )
            )

        # Add the deciles
        traces.extend(deciles_traces)

        # Add the traces to per-practice graph
        graph = dcc.Graph(
            id="graph-{}".format(practice_id),
            figure={
                "data": traces,
                "layout": go.Layout(
                    title="{} orders per 1000 patients at {}".format(
                        " + ".join(test_codes), practice_id
                    ),
                    yaxis={"range": [0, ymax]},
                    xaxis={"range": [months[0], months[-1]]},
                    showlegend=False,
                ),
            },
            config={"staticPlot": False},  # < -- XXX about twice as fast
        )
        graphs.append(graph)
    return html.Div(graphs)
