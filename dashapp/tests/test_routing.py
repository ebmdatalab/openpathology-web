from apps import stateful_routing


def test_list_conversion():
    urls = stateful_routing.url_map.bind("hostname")
    path = urls.build(
        "graph/test_codes/practice_id",
        {"page_id": "frob", "practice_id": 12, "test_codes": ["FBC"]},
        append_unknown=False,
    )
    expected = "/apps/frob/FBC/12"
    assert path == expected

    path = urls.build(
        "graph/test_codes/practice_id",
        {"page_id": "frob", "practice_id": 12, "test_codes": ["FBC", "K"], "frof": "h"},
        append_unknown=False,
    )
    expected = "/apps/frob/FBC+K/12"
    assert path == expected
