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
                if k in state:
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
            logger.debug("  trying endpoint %s for state %s", endpoint, page_state)
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
        Input("denominator-tests-dropdown", "value"),
        Input("test-filter-dropdown", "value"),
    ],
    [State("page-state", "children")],
)
def update_state_from_inputs(
    pathname,
    clickData,
    selected_numerator,
    selected_denominator,
    denominator_tests,
    selected_filter,
    page_state,
):
    """
    Given a series of possible user inputs, update the state if it needs to be changed.
    """
    ctx = dash.callback_context
    triggered_inputs = [x["prop_id"].split(".")[0] for x in ctx.triggered]
    page_state = get_state(page_state)
    logger.info("-- updating state from %s", page_state)

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
    if selected_denominator == "other":
        # We store one of raw, per100 or TEST1+TEST in the URL. We
        # always store that as the `denominators` value in the page
        # state, even though the dropdown for selected_numerator may
        # be `other`. This needs cleaning up! XXX
        stored_denominators = denominator_tests
    else:
        stored_denominators = [selected_denominator]
    update_state(
        page_state,
        numerators=selected_numerator,
        denominators=stored_denominators,
        result_filter=selected_filter,
    )

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
        update_state(page_state, denominators=["per1000"])

    del page_state["_dirty"]
    logger.info("-- updating state from %s, to %s", triggered_inputs, page_state)
    return json.dumps(page_state)


def _create_multi_dropdown_update_func(selector_id, page_state_key):
    """Create a callback function that updates a dropdown from a URL
    """

    def update_multi_dropdown_from_url(pathname):
        """Cause the specified multi dropdown to match the current page location
        """
        logger.info(
            "-- numerator multi dropdown %s being set from URL %s",
            selector_id,
            pathname,
        )
        if pathname:
            # Sometimes None for reasons explained here:
            # https://github.com/plotly/dash/issues/133#issuecomment-330714608
            try:
                _, url_state = urls.match(pathname)
                if page_state_key in url_state:
                    return url_state[page_state_key]
                else:
                    return ""
            except NotFound:
                return ""
        raise PreventUpdate

    return update_multi_dropdown_from_url


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


for selector_id, page_state_key in [
    ("numerators-dropdown", "numerators"),
    ("denominator-tests-dropdown", "denominators"),
    ("test-filter-dropdown", "result_filter"),
]:
    app.callback(Output(selector_id, "value"), [Input("url-from-user", "pathname")])(
        _create_multi_dropdown_update_func(selector_id, page_state_key)
    )


for link_id in ["counts", "deciles", "heatmap"]:
    app.callback(Output(f"{link_id}-link", "href"), [Input("page-state", "children")])(
        _create_link_update_func(link_id)
    )


@app.callback(
    Output("denominators-dropdown", "value"), [Input("url-from-user", "pathname")]
)
def update_denominator_dropdown_from_url(pathname):
    """Cause the numerator dropdown to match the current page location
    """
    logger.info("-- numerator dropdown being set from URL %s", pathname)
    if pathname:
        # Sometimes None for reasons explained here:
        # https://github.com/plotly/dash/issues/133#issuecomment-330714608
        try:
            _, url_state = urls.match(pathname)
            if url_state["denominators"] == ["per1000"] or url_state[
                "denominators"
            ] == ["raw"]:
                logger.info("  setting to %s", url_state["denominators"][0])
                return url_state["denominators"][0]
            else:
                return "other"
        except NotFound:
            return ""
    raise PreventUpdate


@app.callback(
    Output("denominator-tests-dropdown", "style"),
    [Input("denominators-dropdown", "value")],
)
def show_or_hide_denominators_multi_dropdown(denominators_selector):
    if denominators_selector == "other":
        return {"display": "block"}
    else:
        return {"display": "none"}


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
