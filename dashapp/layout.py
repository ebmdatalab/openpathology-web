import dash_core_components as dcc
import dash_html_components as html
import dash_table


def layout(df):
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
            dcc.Link("Go to test counts", href="/apps/counts"),
            html.Br(),
            dcc.Link("Go to deciles", href="/apps/deciles", refresh=False),
            html.Br(),
            dcc.Link("Go to heatmap", href="/apps/heatmap", refresh=False),
            # Dropdown selector
            dcc.Dropdown(
                id="test-selector-dropdown",
                options=[{"label": x, "value": x} for x in df.test_code.unique()],
                value="FBC",
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
