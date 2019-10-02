import apps.deciles
import apps.heatmap
import apps.test_counts
import apps.base

import stateful_routing

from app import app


if __name__ == "__main__":
    app.run_server(debug=True)
