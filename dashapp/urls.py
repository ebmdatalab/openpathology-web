from werkzeug.routing import Map, Rule
from werkzeug.routing import UnicodeConverter


class TestListConverter(UnicodeConverter):
    def to_python(self, value):
        value = super(TestListConverter, self).to_python(value)
        return value.split("+")

    def to_url(self, value):
        if value:
            encoded = [super(TestListConverter, self).to_url(x) for x in value]
            value = "+".join(encoded)
        return value


url_map = Map(
    [
        Rule("/apps/<string:page_id>", endpoint="index"),
        Rule("/apps/<string:page_id>/<int:practice_id>", endpoint="graph/practice_id"),
        Rule("/apps/<string:page_id>/<tests:test_codes>", endpoint="graph/test_codes"),
        Rule(
            "/apps/<page_id>/<tests:test_codes>/<int:practice_id>",
            endpoint="graph/test_codes/practice_id",
        ),
    ],
    converters={"tests": TestListConverter},
)

urls = url_map.bind(
    "hostname"
)  # Required by werkzeug for redirects, although we never use
