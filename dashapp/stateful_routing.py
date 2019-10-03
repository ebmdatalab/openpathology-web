"""This module is responsible for maintaining state for the user, and
ensuring this state is also reflected in the URL.

The state is stored as stringified JSON stored in a hidden div.

"""
import json
import logging
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_html_components as html

from app import app
from werkzeug.routing import NotFound
from werkzeug.routing import BuildError
from urls import url_map
from urls import urls


logger = logging.getLogger(__name__)


def get_state(possible_state_text):
    """Get state from stringifyed JSON, or an empty dict
    """
    try:
        state = json.loads(possible_state_text)
    except (json.decoder.JSONDecodeError, TypeError):
        state = {}
    return state


def update_state(state, **kw):
    """Update `state` with keyword values, if they are different from
    current values

    Returns (changed, state) tuple

    """
    changed = False
    for k, v in kw.items():
        if isinstance(k, list):
            different = len(set(v) - set(state.get(k, []))) > 0
        else:
            different = state.get(k, None) != v
        if different:
            state[k] = v
            changed = True
    return (changed, state)


@app.callback(Output("url-for-update", "pathname"), [Input("page-state", "children")])
def update_url_from_page_state(page_state):
    """Cause the page location to match the current page state
    """
    page_state = get_state(page_state)
    logger.debug("Getting URL from page state %s", page_state)
    url = None
    # Find the last rule (`iter_rules` iterates over the map in
    # reverse order) that can match our state
    for endpoint in [x.endpoint for x in url_map.iter_rules()]:
        try:
            logger.debug("Trying endpoint %s for state %s", endpoint, page_state)
            url = urls.build(endpoint, page_state, append_unknown=False)
            logger.debug("Found url %s", url)
            break
        except BuildError:
            pass
    return url


@app.callback(
    Output("page-state", "children"),
    [
        Input("url-from-user", "pathname"),
        Input("heatmap-graph", "clickData"),
        Input("test-selector-dropdown", "value"),
        Input("test-selector-table", "selected_row_ids"),
    ],
    [State("page-state", "children")],
)
def update_state_from_inputs(
    pathname, clickData, selected_test, selected_row_ids, page_state
):
    """
    Given a series of possible user inputs, update the state if it needs to be changed.
    """
    ctx = dash.callback_context
    triggered_inputs = [x["prop_id"].split(".")[0] for x in ctx.triggered]
    if triggered_inputs == ["url-for-update"]:
        # We have a hack where there's two `Location` elements, one
        # for triggering updates, and one for being changed when the
        # state changes. However, they both fire events when the
        # location bar changes.  Ignore events from the one we treat
        # as write-only.
        raise PreventUpdate

    page_state = get_state(page_state)
    if "error" in page_state:
        # Errors should already have been shown by this point. Reset error state.
        del page_state["error"]
    changed = False
    try:
        if "url-from-user" in triggered_inputs:
            _, url_state = urls.match(pathname)
            changed, page_state = update_state(page_state, **url_state)
        if "heatmap-graph" in triggered_inputs:
            # Hack: extract practice id from chart label data, which looks
            # like this: {'points': [{'curveNumber': 0, 'x': '2016-05-01',
            # 'y': 'practice 84', 'z': 86.10749488562395}]}. I think
            # there's a cleaner way to pass ids as chart metadata
            practice_id = clickData["points"][0]["y"].split(" ")[-1]
            page_state["page_id"] = "deciles"
            changed, page_state = update_state(
                page_state, practice_id=practice_id, page_id="deciles"
            )
        if "test-selector-dropdown" in triggered_inputs:
            changed, page_state = update_state(page_state, test_codes=[selected_test])
        if "test-selector-table" in triggered_inputs:
            changed, page_state = update_state(page_state, test_codes=selected_row_ids)
        if not changed:
            logger.info("State unchanged")
            raise PreventUpdate
    except NotFound:
        page_state["error"] = {
            "status_code": 404,
            "message": f"Unable to find page at {pathname}",
        }
    return json.dumps(page_state)


@app.callback(Output("error-container", "children"), [Input("page-state", "children")])
def show_error_from_page_state(page_state):
    """
    """
    page_state = get_state(page_state)
    if "error" in page_state:
        return [
            html.Div(
                page_state["error"]["message"],
                id="error",
                className="alert alert-danger",
            )
        ]
    else:
        return []