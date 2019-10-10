from werkzeug.routing import Map, Rule, Submount
from werkzeug.routing import UnicodeConverter, BaseConverter


class TestListConverter(UnicodeConverter):
    def to_python(self, value):
        value = super(TestListConverter, self).to_python(value)
        return value.split("+")

    def to_url(self, value):
        if value:
            encoded = [super(TestListConverter, self).to_url(x) for x in value]
            value = "+".join(encoded)
        return value


class AppConverter(BaseConverter):
    regex = r"(?:deciles|heatmap|counts)"


class EntityConverter(BaseConverter):
    regex = r"(?:ccg|practice|lab|test_code)"


url_map = Map(
    [
        Submount(
            "/apps",
            [
                Rule("/<app:page_id>", endpoint="index"),
                Rule(
                    "/<app:page_id>/by/<entity_type:entity_type>/<string:entity_id>/numerators/<tests:numerators>/denominators/<tests:denominators>/filter/<string:result_filter>",
                    endpoint="graph/numerators/denominators/practice_id/filter",
                ),
            ],
        )
    ],
    converters={
        "tests": TestListConverter,
        "app": AppConverter,
        "entity_type": EntityConverter,
    },
)

urls = url_map.bind(
    "hostname"
)  # Required by werkzeug for redirects, although we never use
