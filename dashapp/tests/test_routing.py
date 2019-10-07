import stateful_routing.url_map


def test_list_conversion():
    urls = stateful_routing.url_map.bind("hostname")
    path = urls.build(
        "graph/numerators/practice_id",
        {"page_id": "frob", "practice_id": 12, "numerators": ["FBC"]},
        append_unknown=False,
    )
    expected = "/apps/frob/FBC/12"
    assert path == expected

    path = urls.build(
        "graph/numerators/practice_id",
        {"page_id": "frob", "practice_id": 12, "numerators": ["FBC", "K"], "frof": "h"},
        append_unknown=False,
    )
    expected = "/apps/frob/FBC+K/12"
    assert path == expected
