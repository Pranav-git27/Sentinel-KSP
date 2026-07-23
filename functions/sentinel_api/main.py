"""Sentinel-KSP API application entrypoint.

Creates the central Flask application, enables CORS, registers all route
blueprints, exposes a health-check endpoint, and starts the development
server when executed directly or via Catalyst Advanced Function handler.
"""

import logging
import os
import sys

# Ensure target package directory is importable
_TARGET_DIR = os.path.dirname(os.path.abspath(__file__))
if _TARGET_DIR not in sys.path:
    sys.path.insert(0, _TARGET_DIR)

from flask import Flask, jsonify
from flask_cors import CORS

from routes.auth import auth_bp
from routes.geospatial import geospatial_bp
from routes.link_analysis import link_analysis_bp
from routes.predictive import predictive_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory that assembles and configures the Flask app."""
    app = Flask(__name__)
    CORS(app)

    # Register all feature blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(geospatial_bp)
    app.register_blueprint(link_analysis_bp)
    app.register_blueprint(predictive_bp)

    @app.route("/api/health", methods=["GET"])
    def health():
        """Liveness probe for the API."""
        return jsonify({"status": "healthy"}), 200

    return app


# Module-level WSGI application
app = create_app()


def handler(request):
    """Zoho Catalyst Advanced Function entry point handler.
    
    Passes the incoming Catalyst WSGI/HTTP request context directly to Flask.
    """
    with app.request_context(request.environ):
        return app.full_dispatch_request()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)