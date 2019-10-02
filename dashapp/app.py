import logging
import pandas as pd
import dash
from flask_caching import Cache

from layout import layout
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


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

cache = Cache()
cache.init_app(app.server, config=settings.CACHE_CONFIG)


@cache.memoize()
def get_count_data(sample_size=None):
    """Get anonymised count data by month and test_code and practice
    """
    df = pd.read_csv("cornwall_data_processed_anonymised.csv")

    # Convert month to datetime
    df.loc[:, "month"] = pd.to_datetime(df["month"])

    # estimate errors from data suppression
    df.loc[df["count"] == 3, "error"] = 2
    df["error"].fillna(0, inplace=True)

    # copy anonymised id into column named "practice_id" as an integer
    df = df.loc[pd.notnull(df["anon_id"])]
    df["practice_id"] = df["anon_id"].astype(int)
    df = (
        df[["month", "test_code", "count", "total_list_size", "practice_id", "error"]]
        .groupby(["month", "test_code", "total_list_size", "practice_id"])
        .sum()
        .reset_index()
    )
    df.loc[:, "calc_value"] = df["count"] / df["total_list_size"] * 1000
    df.loc[:, "calc_value_error"] = df["error"] / df["total_list_size"] * 1000
    if sample_size:
        some_practices = df.practice_id.sample(sample_size)
        return df[df.loc[:, "practice_id"].isin(some_practices)]
    else:
        return df


app.layout = layout(get_count_data())
