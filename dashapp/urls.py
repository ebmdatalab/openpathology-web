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
        Rule("/apps/<string:page_id>/<tests:numerators>", endpoint="graph/numerators"),
        Rule(
            "/apps/<string:page_id>/<tests:numerators>/<tests:denominators>",
            endpoint="graph/numerators/denominators",
        ),
        Rule(
            "/apps/<page_id>/<tests:numerators>/<int:practice_id>",
            endpoint="graph/numerators/practice_id",
        ),
        Rule(
            "/apps/<page_id>/<tests:numerators>/<tests:denominators>/<int:practice_id>",
            endpoint="graph/numerators/denominators/practice_id",
        ),
    ],
    converters={"tests": TestListConverter},
)

urls = url_map.bind(
    "hostname"
)  # Required by werkzeug for redirects, although we never use
