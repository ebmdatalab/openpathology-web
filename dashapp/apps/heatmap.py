import logging
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from app import app

from data import get_count_data
from stateful_routing import get_state
import settings

logger = logging.getLogger(__name__)


def sort_by_practice_ids(df):
    """Compute a sort order for the practice charts, based on the mean
    calc_value of the last 6 months.

    Note that we sort in ascending order, because the origin of a
    heatmap is bottom left, and we want the highest values at the top.

    """
    return df.reindex(
        df.fillna(0).iloc[:, -6:].mean(axis=1).sort_values(ascending=True).index, axis=0
    )


@app.callback(Output("heatmap-graph", "figure"), [Input("page-state", "children")])
def update_heatmap(page_state):
    page_state = get_state(page_state)
    if page_state.get("page_id") != settings.HEATMAP_CHART_ID:
        return {}

    test_codes = page_state.get("test_codes", [])
    trace_df = get_count_data(
        numerator=test_codes, denominator=page_state.get("denominator", None)
    )
    vals_by_practice = trace_df.pivot(
        index="practice_id", columns="month", values="calc_value"
    )
    # Sort by mean value of last 6 months
    vals_by_practice = sort_by_practice_ids(vals_by_practice)
    practices = ["practice {}".format(x) for x in vals_by_practice.index]
    # sort with hottest at top
    trace = go.Heatmap(z=vals_by_practice, x=vals_by_practice.columns, y=practices)
    target_rowheight = 20
    height = max(350, target_rowheight * len(practices))
    logger.debug(
        "Target rowheight of {} for {} practices".format(height, len(practices))
    )
    return {
        "data": [trace],
        "layout": go.Layout(
            width=800,
            height=height,
            xaxis={"fixedrange": True},
            yaxis={
                "fixedrange": True,
                "tickmode": "array",
                "tickvals": practices,
                "ticktext": practices,
            },
        ),
    }
