# Navigating the code

* This is a Dash app. Pretty much all the Dash documentation is in the [short tutorial](https://dash.plot.ly/getting-started). This is worth reading in full before getting started.  The docstrings in the code (linke from that documentation) are very thorough.
* Dash is a Flask app that wraps React + Plotly. It runs as a single page app.
* All the charts are Plotly charts, whose best reference is [here](https://plot.ly/python/reference/), although you have to work out how to invoke them in a Dash-like way yourself.


To run the app, run `python index.py`. This sets up a flask app (`app.py`), and imports modules in `apps/`, each providing a particular chart for the single page app.

Per-client state is stored as stringified JSON in a hidden div. Bookmarkable state is mirrored in the location bar of the browser.  This is all handled by `apps/stateful_routing.py`.

When a chart element (defined in `layouts.py` changes, its state flows to the `stateful_routing` module and the location bar; the various charts are wired to changes in the per-client state and update accordingly. Charts that are not currently being viewed are hidden (see `apps/base.py`), as Dash requires everything wired up for callbacks to be present on the page.

# Is Dash a good choice?

Probably, enough to give it a proper change.

Benefits:

* Very expressive, terse code
* Plotly charts feel nicer than Highcharts. It is easier to get data in the right format and finding the options we want to use is easier

Costs:

* Not a full framework: have had to handle URL / state / multipage stuff ourselves (see `stateful_routing.py`)

## Performance

Displaying 86 charts on a fast laptop takes around 15s. This time is
halved if you remove all interactivity from the charts.

There may be further performance improvements from selectively removing interactivity.

There also seems to be an opportunity to cut down the time inside plotly-py; 25% of the time is spent in a string validator ([look at this as HTML in a browser](https://gist.github.com/sebbacon/00dbf2c3b1cd25b6762d003806cb8f2e))

Currently the same thing takes about 45s on OpenPrescribing, though
probably 40s of this is network time; the main concern with Dash here
is that it chews a lot of CPU. We would probably want to implement a
smooth-scroll handler for this, per [these notes](https://community.plot.ly/t/scroll-position/4618)



## Next steps

Scratchpad:

* Think about the actual useful design:
  * We have per 1000 or selection of tests as a denominator
  * We have count of tests or count inside/outside reference range as numerator
    *  Could also do *within* reference range
  * A user will first build a measure, which is a multi-select for numerators and a multi-select for denominators
  * They can then optionally save the measure
  * This means it must be possible to bookmark any measure
  * We then want to show X entity in the context of Y, so that would practices in the context of england or practices in the context of CCGs or CCGs in the context of England
  * Deciles would always be based on X. Y would drive the dropdowns atthe top of each page and allow you to switch between them.

* What does this require of the data? I need to run off the raw data and make calc_value on the fly. We could allow the user to select "over range", "under range", and "error".