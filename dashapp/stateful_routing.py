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
    current values. Keyword values of None or empty lists denote that
    the key should be removed from the state.

    Sets a `_dirty` key if any changes have been made
    """
    changed = False
    for k, v in kw.items():
        if isinstance(v, list):
            v = [x for x in v if x]  # Falsey values get deleted
            if not v and k not in state:
                different = False
            else:
                different = len(set(v).symmetric_difference(set(state.get(k, [])))) > 0
        else:
            different = state.get(k, "_nevermatches_") != v
        if different:
            if not v:
                del state[k]
            else:
                state[k] = v
            changed = True
    if changed:
        state["_dirty"] = True


def _url_from_state(page_state):
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
    if not url:
        logger.debug("No url found for state %s; PreventUpdate", page_state)
        raise PreventUpdate
    return url


@app.callback(Output("url-for-update", "pathname"), [Input("page-state", "children")])
def update_url_from_page_state(page_state):
    """Cause the page location to match the current page state
    """
    page_state = get_state(page_state)
    logger.debug("Getting URL from page state %s", page_state)
    return _url_from_state(page_state)


@app.callback(
    Output("page-state", "children"),
    [
        Input("url-from-user", "pathname"),
        Input("heatmap-graph", "clickData"),
        Input("numerators-dropdown", "value"),
        Input("denominators-dropdown", "value"),
    ],
    [State("page-state", "children")],
)
def update_state_from_inputs(
    pathname, clickData, selected_numerator, selected_denominator, page_state
):
    """
    Given a series of possible user inputs, update the state if it needs to be changed.
    """
    ctx = dash.callback_context
    triggered_inputs = [x["prop_id"].split(".")[0] for x in ctx.triggered]
    logger.info("-- updating state from %s", triggered_inputs)
    page_state = get_state(page_state)

    # Errors should already have been shown by this point. Reset error state.
    if "error" in page_state:
        del page_state["error"]
    try:
        _, url_state = urls.match(pathname)
        update_state(page_state, **url_state)
    except NotFound:
        update_state(
            page_state,
            error={"status_code": 404, "message": f"Unable to find page at {pathname}"},
        )

    update_state(page_state, numerators=[selected_numerator])
    update_state(page_state, denominators=[selected_denominator])

    if "heatmap-graph" in triggered_inputs:
        # Hack: extract practice id from chart label data, which looks
        # like this: {'points': [{'curveNumber': 0, 'x': '2016-05-01',
        # 'y': 'practice 84', 'z': 86.10749488562395}]}. I think
        # there's a cleaner way to pass ids as chart metadata
        practice_id = clickData["points"][0]["y"].split(" ")[-1]
        page_state["page_id"] = "deciles"
        update_state(page_state, practice_id=practice_id, page_id="deciles")

    # Only trigger state changes if something has changed
    if "_dirty" not in page_state:
        logger.info("State unchanged")
        raise PreventUpdate

    # add default numerators and denonimators
    if "numerators" not in page_state:
        update_state(page_state, numerators=["all"])
    if "denominators" not in page_state:
        update_state(page_state, denominators=["raw"])

    del page_state["_dirty"]
    logger.info("-- updating state from %s, to %s", triggered_inputs, page_state)
    return json.dumps(page_state)


def _create_dropdown_update_func(selector_id):
    """Create a callback function that updates a dropdown from a URL
    """

    def update_numerator_dropdown_from_url(pathname):
        """Cause the numerator dropdown to match the current page location
        """
        logger.info("-- numerator dropdown being set from URL %s", pathname)
        if pathname:
            # Sometimes None for reasons explained here:
            # https://github.com/plotly/dash/issues/133#issuecomment-330714608
            try:
                _, url_state = urls.match(pathname)
                if selector_id in url_state:
                    return url_state[selector_id][0]
                else:
                    return ""
            except NotFound:
                return ""
        raise PreventUpdate

    return update_numerator_dropdown_from_url


def _create_link_update_func(selector_id):
    """Create a callback function that updates a dropdown from a URL
    """

    def update_link_from_state(page_state):
        """Substitute page_id in a given link with that found in the page_state
        """
        page_state = get_state(page_state)
        page_state["page_id"] = selector_id
        return _url_from_state(page_state)

    return update_link_from_state


for selector_id in ["numerators", "denominators"]:
    app.callback(
        Output(f"{selector_id}-dropdown", "value"), [Input("url-from-user", "pathname")]
    )(_create_dropdown_update_func(selector_id))


for link_id in ["counts", "deciles", "heatmap"]:
    app.callback(Output(f"{link_id}-link", "href"), [Input("page-state", "children")])(
        _create_link_update_func(link_id)
    )


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
