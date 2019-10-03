from pathlib import Path

# A list of all the charts that appear in the app
HEATMAP_CHART_ID = "heatmap"
DECILES_CHART_ID = "deciles"
COUNTS_CHART_ID = "counts"
CHARTS = [HEATMAP_CHART_ID, DECILES_CHART_ID, COUNTS_CHART_ID]

CSV_DIR = Path(__file__).parents[0] / "data_csvs"

CACHE_CONFIG = {
    # Use Redis in production?
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": "/tmp/",
}