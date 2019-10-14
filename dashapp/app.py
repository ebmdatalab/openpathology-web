import logging
import dash
import dash_bootstrap_components as dbc
from flask_caching import Cache
import settings

logging.basicConfig(
    filename="openpath_dash.log",
    level=logging.DEBUG,
    format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)


external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash("openpath", external_stylesheets=external_stylesheets)
cache = Cache()
cache.init_app(app.server, config=settings.CACHE_CONFIG)
