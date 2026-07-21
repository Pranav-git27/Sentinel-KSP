"""Application configuration and Zoho Catalyst SDK initialization.

This module initializes the Zoho Catalyst SDK once at import time and exposes
helpers used by the REST routes:

* ``get_zcql_service()`` - returns the ZCQL (Catalyst Query Language) service
  used to execute SQL-like queries against the Catalyst datastore.
* ``escape_zcql_string()`` - safely quotes a value for embedding in a ZCQL
  string literal, mitigating injection through user-supplied input.
"""

import logging

import zcatalyst_sdk

logger = logging.getLogger(__name__)

# The base exception type exposed by the SDK. Import defensively so the
# module still loads across SDK versions where the class may live elsewhere.
try:
    from zcatalyst_sdk import CatalystException
except ImportError:  # pragma: no cover - defensive guard for SDK differences
    CatalystException = Exception


# Initialize the Catalyst SDK a single time. The SDK reads project
# credentials from the Catalyst environment / catalyst.json configuration.
try:
    app = zcatalyst_sdk.initialize()
    logger.info("Zoho Catalyst SDK initialized successfully.")
except CatalystException as exc:
    logger.exception("Failed to initialize the Zoho Catalyst SDK: %s", exc)
    app = None
except Exception as exc:  # pragma: no cover - defensive guard
    logger.exception("Unexpected error initializing the Zoho Catalyst SDK: %s", exc)
    app = None


def get_zcql_service():
    """Return the Catalyst ZCQL service.

    The ZCQL service is used to execute SQL-like queries against the Catalyst
    datastore tables. This helper centralizes initialization and error handling
    so route modules can simply call ``get_zcql_service()`` and focus on their
    queries.

    Returns:
        zcatalyst_sdk.ZCQLService: The ZCQL service instance.

    Raises:
        RuntimeError: If the Catalyst SDK failed to initialize or the ZCQL
            service cannot be obtained.
    """
    if app is None:
        raise RuntimeError("Zoho Catalyst SDK is not initialized.")
    try:
        return app.zcql()
    except CatalystException as exc:
        logger.exception("Failed to obtain the ZCQL service: %s", exc)
        raise RuntimeError("Unable to obtain the ZCQL service.") from exc


def escape_zcql_string(value):
    """Return a safely-quoted ZCQL string literal for the given value.

    Single quotes within the value are doubled (the standard SQL escape
    sequence) so that user-supplied identifiers cannot break out of the
    string literal when interpolated into a ZCQL query.

    Args:
        value: The value to quote. ``None`` becomes an empty string literal.

    Returns:
        str: A quoted ZCQL string literal, e.g. ``'KSP-12345'``.
    """
    if value is None:
        return "''"
    safe = str(value).replace("'", "''")
    return "'{}'".format(safe)
