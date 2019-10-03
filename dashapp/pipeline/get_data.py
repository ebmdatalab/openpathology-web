"""Get a list of test codes and names that have been mapped between all labs
"""
import pandas as pd
from pathlib import Path
import settings
from flask import Flask

app = Flask(__name__)


@app.cli.command("get_codes")
def get_codes():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeLPEW4rTy_hCktuAXEsXtivcdREDuU7jKfXlvJ7CTEBycrxWyunBWdLgGe7Pm1A/pub?gid=241568377&single=true&output=csv"
    target_path = settings.CSV_DIR / "test_codes.csv"
    df = pd.read_csv(url)
    df[df["show_in_app?"] == True][["datalab_testcode", "testname"]].to_csv(
        target_path, index=False
    )
