"""Sentinel-KSP API application entrypoint.

Creates the central Flask application, enables CORS, registers all route
blueprints, exposes health-check endpoints, and provides a small Catalyst REST
client for local backend development.
"""

from datetime import datetime, timezone
import logging
import os
import sys
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv()

# Ensure target package directory is importable.
_TARGET_DIR = os.path.dirname(os.path.abspath(__file__))
if _TARGET_DIR not in sys.path:
    sys.path.insert(0, _TARGET_DIR)

from routes.auth import auth_bp
from routes.geospatial import geospatial_bp
from routes.link_analysis import link_analysis_bp
from routes.predictive import predictive_bp

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class CatalystClientError(RuntimeError):
    """Raised when Catalyst REST access cannot be completed."""


class CatalystClient:
    """Minimal Zoho Catalyst REST client backed by a refresh-token OAuth flow."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        project_id: str | None = None,
        accounts_url: str | None = None,
        project_domain: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.client_id = client_id or os.getenv("ZC_SDK_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("ZC_SDK_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("ZC_SDK_REFRESH_TOKEN")
        self.project_id = project_id or os.getenv("CATALYST_PROJECT_ID")
        self.accounts_url = (accounts_url or os.getenv("ZOHO_ACCOUNTS_URL") or "https://accounts.zoho.in").rstrip("/")
        self.project_domain = (project_domain or os.getenv("CATALYST_PROJECT_DOMAIN") or "https://api.catalyst.zoho.in").rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._access_token: str | None = None

    def _missing_config(self) -> list[str]:
        required_values = {
            "ZC_SDK_CLIENT_ID": self.client_id,
            "ZC_SDK_CLIENT_SECRET": self.client_secret,
            "ZC_SDK_REFRESH_TOKEN": self.refresh_token,
            "CATALYST_PROJECT_ID": self.project_id,
        }
        return [name for name, value in required_values.items() if not value]

    def _ensure_configured(self) -> None:
        missing = self._missing_config()
        if missing:
            message = f"Missing required Catalyst environment variables: {', '.join(missing)}"
            logger.error(message)
            raise CatalystClientError(message)

    def get_access_token(self) -> str:
        """Exchange the configured refresh token for a short-lived OAuth access token."""
        if self._access_token:
            return self._access_token

        self._ensure_configured()
        token_url = f"{self.accounts_url}/oauth/v2/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            response = requests.post(token_url, data=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("Failed to generate Catalyst OAuth access token")
            raise CatalystClientError("Failed to generate Catalyst OAuth access token") from exc

        try:
            token_data = response.json()
        except ValueError as exc:
            logger.exception("Catalyst OAuth response was not valid JSON")
            raise CatalystClientError("Catalyst OAuth response was not valid JSON") from exc

        access_token = token_data.get("access_token")
        if not access_token:
            logger.error("Catalyst OAuth response did not include an access_token")
            raise CatalystClientError("Catalyst OAuth response did not include an access_token")

        self._access_token = access_token
        return access_token

    def fetch_all_rows(self, table_name: str) -> list[dict[str, Any]]:
        """Fetch all rows from a Catalyst Data Store table by table name."""
        if not table_name:
            raise ValueError("table_name is required")

        access_token = self.get_access_token()
        url = f"{self.project_domain}/baas/v1/project/{self.project_id}/table/{table_name}/row"
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

        try:
            response = requests.get(url, headers=headers, timeout=self.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("Failed to fetch Catalyst rows for table '%s'", table_name)
            raise CatalystClientError(f"Failed to fetch Catalyst rows for table '{table_name}'") from exc

        try:
            response_data = response.json()
        except ValueError as exc:
            logger.exception("Catalyst Data Store response was not valid JSON for table '%s'", table_name)
            raise CatalystClientError("Catalyst Data Store response was not valid JSON") from exc

        if response_data.get("status") != "success":
            logger.error("Catalyst Data Store returned an unsuccessful response: %s", response_data)
            raise CatalystClientError("Catalyst Data Store returned an unsuccessful response")

        rows = response_data.get("data", [])
        if not isinstance(rows, list):
            logger.error("Catalyst Data Store response data was not a list: %s", response_data)
            raise CatalystClientError("Catalyst Data Store response data was not a list")

        return rows


def create_app():
    """Application factory that assembles and configures the Flask app."""
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register all feature blueprints.
    app.register_blueprint(auth_bp)
    app.register_blueprint(geospatial_bp)
    app.register_blueprint(link_analysis_bp)
    app.register_blueprint(predictive_bp)

    @app.route("/", methods=["GET"])
    def root_health():
        """Base liveness probe for the API."""
        return jsonify({
            "service": "sentinel-audit-api",
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200

    @app.route("/api/health", methods=["GET"])
    def health():
        """Backward-compatible liveness probe for the API."""
        return root_health()

    return app


# Module-level WSGI application.
app = create_app()


def handler(request):
    """Zoho Catalyst Advanced Function entry point handler.

    Passes the incoming Catalyst WSGI/HTTP request context directly to Flask.
    """
    with app.request_context(request.environ):
        return app.full_dispatch_request()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)