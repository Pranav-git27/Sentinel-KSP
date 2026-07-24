"""Application configuration and Zoho Catalyst SDK initialization."""



import os

import time

from typing import Any, Dict, List, Optional



import requests

import zcatalyst_sdk



# ---------------------------------------------------------------------------

# SDK Initialization

# ---------------------------------------------------------------------------

app = None



# ---------------------------------------------------------------------------

# OAuth token cache for direct Zoho Catalyst REST API calls

# ---------------------------------------------------------------------------

_ZOHO_ACCESS_TOKEN: Optional[str] = None

_ZOHO_ACCESS_TOKEN_EXPIRES_AT: float = 0.0

_ZOHO_TOKEN_EXPIRY_SAFETY_SECONDS = 120

_ZOHO_DEFAULT_TOKEN_TTL_SECONDS = 3600





def _init_sdk():

    """Initialize the Catalyst SDK while preserving cloud-context fallback behavior."""

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

                environment=os.getenv("CATALYST_ENV", "Development"),

                project_domain=f"https://api.catalyst.zoho.in/baas/v1/project/{project_id}",

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





def _get_zoho_access_token() -> str:

    """

    Return a valid Zoho OAuth access token for direct Catalyst REST API calls.



    The token is generated from the configured self-client refresh token and cached

    in memory until shortly before expiry to avoid unnecessary token requests.

    """

    global _ZOHO_ACCESS_TOKEN, _ZOHO_ACCESS_TOKEN_EXPIRES_AT



    now = time.time()

    if _ZOHO_ACCESS_TOKEN and now < _ZOHO_ACCESS_TOKEN_EXPIRES_AT:

        return _ZOHO_ACCESS_TOKEN



    client_id = os.getenv("ZC_SDK_CLIENT_ID")

    client_secret = os.getenv("ZC_SDK_CLIENT_SECRET")

    refresh_token = os.getenv("ZC_SDK_REFRESH_TOKEN")



    missing = [

        name

        for name, value in (

            ("ZC_SDK_CLIENT_ID", client_id),

            ("ZC_SDK_CLIENT_SECRET", client_secret),

            ("ZC_SDK_REFRESH_TOKEN", refresh_token),

        )

        if not value

    ]

    if missing:

        raise RuntimeError(

            "Cannot generate Zoho OAuth access token. Missing required environment "

            f"variable(s): {', '.join(missing)}."

        )



    token_url = "https://accounts.zoho.in/oauth/v2/token"

    payload = {

        "refresh_token": refresh_token,

        "client_id": client_id,

        "client_secret": client_secret,

        "grant_type": "refresh_token",

    }



    try:

        response = requests.post(token_url, data=payload, timeout=30)

    except requests.RequestException as exc:

        raise RuntimeError(f"Failed to request Zoho OAuth access token: {exc}") from exc



    response_body = response.text

    try:

        token_payload: Dict[str, Any] = response.json()

    except ValueError as exc:

        raise RuntimeError(

            "Zoho OAuth token endpoint returned a non-JSON response "

            f"(HTTP {response.status_code}): {response_body[:500]}"

        ) from exc



    if response.status_code >= 400:

        raise RuntimeError(

            "Zoho OAuth token endpoint rejected the refresh token request "

            f"(HTTP {response.status_code}): {token_payload}"

        )



    access_token = token_payload.get("access_token")

    if not isinstance(access_token, str) or not access_token.strip():

        raise RuntimeError(f"Zoho OAuth token response did not include access_token: {token_payload}")



    expires_in_raw = token_payload.get("expires_in", _ZOHO_DEFAULT_TOKEN_TTL_SECONDS)

    try:

        expires_in = int(expires_in_raw)

    except (TypeError, ValueError):

        expires_in = _ZOHO_DEFAULT_TOKEN_TTL_SECONDS



    cache_ttl = max(0, expires_in - _ZOHO_TOKEN_EXPIRY_SAFETY_SECONDS)

    _ZOHO_ACCESS_TOKEN = access_token.strip()

    _ZOHO_ACCESS_TOKEN_EXPIRES_AT = now + cache_ttl



    return _ZOHO_ACCESS_TOKEN





def get_zcql_service():

    """Return the Catalyst ZCQL service instance for backward compatibility."""

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





def fetch_all_rows(table_name: str) -> List[Dict[str, Any]]:

    """Fetch all rows from a Catalyst Data Store table using direct REST ZCQL."""

    normalized_table_name = str(table_name or "").strip()

    if not normalized_table_name or not normalized_table_name.replace("_", "").isalnum():

        raise ValueError("table_name must be a valid, non-empty table identifier")



    project_id = os.getenv("CATALYST_PROJECT_ID")

    if not project_id:

        raise RuntimeError("Cannot execute REST ZCQL query. Missing CATALYST_PROJECT_ID.")



    access_token = _get_zoho_access_token()

    query_str = f"SELECT * FROM {normalized_table_name}"

    endpoint = f"https://api.catalyst.zoho.in/baas/v1/project/{project_id}/query"

    headers = {

        "Authorization": f"Zoho-oauthtoken {access_token}",

        "Environment": os.getenv("CATALYST_ENV", "Development"),

        "Content-Type": "application/json",

    }

    payload = {"query": query_str}



    try:

        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)

    except requests.RequestException as exc:

        raise RuntimeError(

            f"REST ZCQL request failed for table '{normalized_table_name}': {exc}"

        ) from exc



    response_body = response.text

    try:

        response_payload: Dict[str, Any] = response.json()

    except ValueError as exc:

        raise RuntimeError(

            f"REST ZCQL returned a non-JSON response for table '{normalized_table_name}' "

            f"(HTTP {response.status_code}): {response_body[:500]}"

        ) from exc



    if response.status_code >= 400:

        raise RuntimeError(

            f"REST ZCQL query failed for table '{normalized_table_name}' "

            f"(HTTP {response.status_code}): {response_payload}"

        )



    data = response_payload.get("data", [])

    if data is None:

        data = []

    if not isinstance(data, list):

        raise RuntimeError(

            f"REST ZCQL response for table '{normalized_table_name}' has invalid data payload: "

            f"{type(data).__name__}"

        )



    rows: List[Dict[str, Any]] = []

    for item in data:

        if not isinstance(item, dict):

            continue



        row = item.get(normalized_table_name, item)

        if isinstance(row, dict):

            rows.append(row)

        else:

            rows.append({normalized_table_name: row})



    print(f"[REST ZCQL] Fetched {len(rows)} rows for {normalized_table_name}")

    return rows 

