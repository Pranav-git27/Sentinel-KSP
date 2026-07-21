"""Sentinel-KSP API application entrypoint.

Creates the central Flask application, enables CORS, registers all route
blueprints, exposes a health-check endpoint, and starts the development
server when executed directly.
"""

import logging
import os
import sys

# Ensure the target package directory is importable regardless of the
# current working directory (local dev from the repo root vs. a Catalyst
# deployment where this folder is the function root).
_TARGET_DIR = os.path.dirname(os.path.abspath(__file__))
if _TARGET_DIR not in sys.path:
    sys.path.insert(0, _TARGET_DIR)

from flask import Flask, jsonify  # noqa: E402
from flask_cors import CORS  # noqa: E402

from routes.auth import auth_bp  # noqa: E402
from routes.geospatial import geospatial_bp  # noqa: E402
from routes.link_analysis import link_analysis_bp  # noqa: E402
from routes.predictive import predictive_bp  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory that assembles and configures the Flask app.

    Returns:
        flask.Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    CORS(app)

    # Register all feature blueprints.
    app.register_blueprint(auth_bp)
    app.register_blueprint(geospatial_bp)
    app.register_blueprint(link_analysis_bp)
    app.register_blueprint(predictive_bp)

    @app.route("/api/health", methods=["GET"])
    def health():
        """Liveness probe for the API."""
        return jsonify({"status": "healthy"}), 200

    return app


# Module-level WSGI application for production / serverless runners.
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
