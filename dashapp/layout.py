import dash_core_components as dcc
import dash_html_components as html
import dash_table


def layout(tests_df):
    tests_df.columns = ["value", "label"]
    return html.Div(
        [
            # Hidden div inside the app that stores the page state
            html.Pre(id="page-state", style={"display": "none"}),
            # Two "locations" with the same function, to allow two
            # different callbacks to use them.  Unfortunately they both get triggered.
            dcc.Location(id="url-from-user", refresh=False),
            dcc.Location(id="url-for-update", refresh=False),
            # Navigation
            # XXX use routed URLs here!
            dcc.Link("Go to test counts", id="counts-link", href="/apps/counts"),
            html.Br(),
            dcc.Link(
                "Go to deciles", id="deciles-link", href="/apps/deciles", refresh=False
            ),
            html.Br(),
            dcc.Link(
                "Go to heatmap", id="heatmap-link", href="/apps/heatmap", refresh=False
            ),
            # Dropdown selector
            html.Label("Numerators"),
            dcc.Dropdown(
                id="numerators-dropdown",
                multi=True,
                # XXX use clientside javascript to make "all tests"
                # disappear if you select just one:
                # https://community.plot.ly/t/dash-0-41-0-released/22131
                options=[{"value": "all", "label": "All tests"}]
                + tests_df.to_dict("records"),
            ),
            html.Label("Denominators"),
            dcc.Dropdown(
                id="denominators-dropdown",
                options=[
                    {"value": "per1000", "label": "Per 1000 patients"},
                    {"value": "raw", "label": "Raw numbers"},
                    {"value": "other", "label": "As a proportion of other tests"},
                ],
            ),
            dcc.Dropdown(
                id="denominator-tests-dropdown",
                multi=True,
                placeholder="Select tests",
                options=tests_df.to_dict("records"),
                style={"display": "none"},
            ),
            html.Label("Filter"),
            dcc.Dropdown(
                id="test-filter-dropdown",
                options=[
                    {"value": "all", "label": "All tests with results"},
                    {
                        "value": "within_range",
                        "label": "Results within reference range",
                    },
                    {"value": "under_range", "label": "Results under reference range"},
                    {"value": "over_range", "label": "Results over reference range"},
                    {
                        "value": "error",
                        "label": "Results with non-numeric values (often errors)",
                    },
                ],
            ),
            html.Div(id="error-container"),
            # All the charts we're interested in, in a spinner container
            dcc.Loading(
                id="loading-heatmap",
                children=[
                    # We make empty graph objects for every graph we might
                    # draw, and show/hide them based on current state
                    html.Div(
                        id="heatmap-container",
                        style={"display": "none"},
                        children=[dcc.Graph(id="heatmap-graph")],
                    ),
                    html.Div(
                        id="counts-container",
                        style={"display": "none"},
                        children=[
                            dcc.Graph(id="counts-graph"),
                            dash_table.DataTable(
                                id="test-selector-table",
                                columns=[
                                    {"name": "test_code", "id": "test_code"},
                                    {"name": "count", "id": "count"},
                                ],
                                sort_action="native",
                                row_selectable="multi",
                            ),
                        ],
                    ),
                    html.Div(id="deciles-container", style={"display": "block"}),
                ],
            ),
        ]
    )
