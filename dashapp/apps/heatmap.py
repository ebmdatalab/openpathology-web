import logging
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from app import app

from data import get_count_data
from stateful_routing import get_state
import settings

logger = logging.getLogger(__name__)


def sort_by_index(df):
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

    numerators = page_state.get("numerators", [])
    denominators = page_state.get("denominators", [])
    result_filter = page_state.get("result_filter", [])
    entity_type = page_state.get("entity_type", None)
    if entity_type == "practice":
        col_name = "practice_id"
    elif entity_type == "test_code":
        col_name = entity_type
    trace_df = get_count_data(
        numerators=numerators,
        denominators=denominators,
        result_filter=result_filter,
        by=col_name,
    )
    vals_by_entity = trace_df.pivot(
        index=col_name, columns="month", values="calc_value"
    )
    # Sort by mean value of last 6 months
    vals_by_entity = sort_by_index(vals_by_entity)
    entities = ["entity {}".format(x) for x in vals_by_entity.index]
    # sort with hottest at top
    trace = go.Heatmap(z=vals_by_entity, x=vals_by_entity.columns, y=entities)
    target_rowheight = 20
    height = max(350, target_rowheight * len(entities))
    logger.debug(
        "Target rowheight of {} for {} {}s".format(height, len(entities), entity_type)
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
                "tickvals": entities,
                "ticktext": entities,
            },
        ),
    }
