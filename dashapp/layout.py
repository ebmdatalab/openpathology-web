import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_bootstrap_components as dbc


def layout(tests_df, ccgs_list):
    tests_df.columns = ["value", "label"]  # XXX refactor
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(
                dbc.NavLink("Top-level counts", id="counts-link", href="/apps/counts")
            ),
            dbc.NavItem(
                dbc.NavLink(
                    "Compare using deciles", id="deciles-link", href="/apps/deciles"
                )
            ),
            dbc.NavItem(
                dbc.NavLink(
                    "Compare using heatmap", id="heatmap-link", href="/apps/heatmap"
                )
            ),
        ],
        brand="OpenPathology",
        brand_href="#",
        sticky="top",
    )
    state_components = html.Div(
        [
            # Hidden div inside the app that stores the page state
            # XXX possibly use https://dash.plot.ly/dash-core-components/store
            html.Pre(id="page-state", style={"display": "none"}),
            # Two "locations" with the same function, to allow two
            # different callbacks to use them without cycles in the graph.
            dcc.Location(id="url-from-user", refresh=False),
            dcc.Location(id="url-for-update", refresh=False),
        ]
    )
    numerators_form = dbc.FormGroup(
        [
            dbc.Label("Numerators"),
            dcc.Dropdown(
                id="numerators-dropdown",
                multi=True,
                # XXX use clientside javascript to make "all tests"
                # disappear if you select just one:
                # https://community.plot.ly/t/dash-0-41-0-released/22131
                options=[{"value": "all", "label": "All tests"}]
                + tests_df.to_dict("records"),
            ),
        ]
    )
    filters_form = dbc.FormGroup(
        [
            dbc.Label("Which test results?"),
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
        ]
    )
    denominators_form = dbc.FormGroup(
        [
            dbc.Label("Denominators"),
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
        ]
    )
    groupby_form = dbc.FormGroup(
        [
            dbc.Label("Group by"),
            dcc.Dropdown(
                id="groupby-dropdown",
                options=[
                    {"value": "practice", "label": "Practice"},
                    {"value": "test_code", "label": "Test code"},
                    {"value": "ccg_id", "label": "CCG"},
                ],
            ),
        ]
    )
    ccg_filter_form = dbc.FormGroup(
        [
            dbc.Label("Showing which CCGs?"),
            dcc.Dropdown(
                id="ccg-dropdown",
                multi=True,
                options=[{"value": "all", "label": "All CCGs"}] + ccgs_list,
            ),
        ]
    )
    form = dbc.Container(
        dbc.Row(
            [
                dbc.Col([numerators_form, denominators_form, groupby_form]),
                dbc.Col([filters_form, ccg_filter_form]),
            ]
        )
    )
    body = dbc.Container(
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.Div(id="description-container"),
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
                                    children=[dcc.Graph(id="counts-graph")],
                                ),
                                html.Div(
                                    id="deciles-container", style={"display": "block"}
                                ),
                            ],
                        ),
                    ]
                )
            )
        )
    )
    return html.Div([navbar, state_components, form, body])
