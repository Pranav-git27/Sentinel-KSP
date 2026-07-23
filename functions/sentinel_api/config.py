"""Application configuration and Zoho Catalyst SDK initialization."""

import json
import logging
import os
import zcatalyst_sdk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SDK Initialization
# ---------------------------------------------------------------------------
app = None

def _init_sdk():
    global app
    
    # Priority 1: Check if app already initialized in memory
    try:
        app = zcatalyst_sdk.get_app()
        if app:
            return app
    except Exception:
        pass

    # Priority 2: Local initialization with Self Client Refresh Token
    client_id = os.getenv("ZC_SDK_CLIENT_ID")
    client_secret = os.getenv("ZC_SDK_CLIENT_SECRET")
    refresh_token = os.getenv("ZC_SDK_REFRESH_TOKEN")
    project_id = os.getenv("CATALYST_PROJECT_ID")
    project_key = os.getenv("CATALYST_PROJECT_KEY") or os.getenv("ZAID")

    if project_id and refresh_token and project_key:
        try:
            from zcatalyst_sdk import credentials
            from zcatalyst_sdk.types import ICatalystOptions

            cred_dict = {
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            }
            catalyst_credential = credentials.RefreshTokenCredential(cred_dict)

            options = ICatalystOptions(
                project_id=str(project_id),
                project_key=str(project_key),
                project_domain="https://api.catalyst.zoho.in",
                environment=os.getenv("CATALYST_ENV", "Development")
            )
            app = zcatalyst_sdk.initialize_app(catalyst_credential, options)
            print(f"[CONFIG] Zoho Catalyst SDK initialized locally (Project ID: {project_id})")
            return app
        except Exception as exc:
            print(f"[CONFIG] Local SDK init failed: {exc}")

    # Priority 3: Cloud Context Initialization
    try:
        app = zcatalyst_sdk.initialize()
        print("[CONFIG] Zoho Catalyst SDK initialized via Cloud context.")
        return app
    except Exception as exc:
        print(f"[CONFIG] Cloud SDK init bypassed: {exc}")

    return None

app = _init_sdk()


def get_zcql_service():
    """Return the Catalyst ZCQL service instance."""
    global app
    if app is None:
        app = _init_sdk()
        
    if app is None:
        raise RuntimeError(
            "Zoho Catalyst SDK is not initialized. Ensure CATALYST_PROJECT_ID, "
            "CATALYST_PROJECT_KEY, ZC_SDK_CLIENT_ID, ZC_SDK_CLIENT_SECRET, and "
            "ZC_SDK_REFRESH_TOKEN are set in your .env file."
        )
    return app.zcql()


def escape_zcql_string(value):
    """Return a safely-quoted ZCQL string literal for the given value."""
    if value is None:
        return "''"
    safe = str(value).replace("'", "''")
    return f"'{safe}'"