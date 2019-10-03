def setup_app_and_layout():
    from app import app
    from layout import layout
    from data import get_test_list

    app.layout = layout(get_test_list())
    return app


def setup_callbacks():
    import apps.base
    import apps.deciles
    import apps.heatmap
    import apps.test_counts

    import stateful_routing


if __name__ == "__main__":
    app = setup_app_and_layout()
    # You can't set up callbacks until the layout has been registered
    setup_callbacks()
    app.run_server(debug=True)
