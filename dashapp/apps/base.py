"""Callbacks that apply to all pages
"""
from dash.dependencies import Input, Output

from app import app
from stateful_routing import get_state
import settings


# for each chart, generate a function to show only that chart
def _create_show_chart_func(chart):
    """creates a callback function"""

    def show_chart(page_state):
        page_state = get_state(page_state)
        if page_state.get("page_id") == chart:
            return {"display": "block"}
        else:
            return {"display": "none"}

    return show_chart


# Register callbacks such that when the page state changes, only the
# page id currently indicated in the page state is shown
for chart in settings.CHARTS:
    app.callback(
        Output("{}-container".format(chart), "style"), [Input("page-state", "children")]
    )(_create_show_chart_func(chart))