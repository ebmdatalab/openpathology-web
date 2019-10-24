import logging
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from app import app
from apps.base import get_chart_title

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
    vals_by_entity = sort_by_index(
        trace_df.pivot(index=col_name, columns="month", values="calc_value")
    )
    # Get labels and order them identically to the values
    labels_by_entity = trace_df.pivot(
        index=col_name, columns="month", values="label"
    ).reindex(vals_by_entity.index)

    entities = ["entity {}".format(x) for x in vals_by_entity.index]
    # sort with hottest at top
    trace = go.Heatmap(
        z=vals_by_entity,
        x=vals_by_entity.columns,
        y=entities,
        text=labels_by_entity,
        hoverinfo="text",
    )
    target_rowheight = 20
    height = max(350, target_rowheight * len(entities))
    logger.debug(
        "Target rowheight of {} for {} {}s".format(height, len(entities), groupby)
    )
    entity_id = f"{col_name}s"
    title = get_chart_title(numerators, denominators, result_filter, entity_id)

    return {
        "data": [trace],
        "layout": go.Layout(
            title=title,
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
