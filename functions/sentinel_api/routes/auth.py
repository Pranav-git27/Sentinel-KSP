"""Authentication routes for the Sentinel-KSP API.

Provides the ``auth_bp`` blueprint which handles officer login. On a login
request any previously active sessions for the officer are deactivated
(``IsActive = false``) so that only a single active session is maintained
at a time.
"""

import logging

from flask import Blueprint, jsonify, request

from config import escape_zcql_string, get_zcql_service

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate an officer and deactivate prior active sessions.

    Reads the officer identifier from the JSON request body, queries the
    ``ActiveSessions`` table for any rows where ``IsActive = true`` for that
    officer, and updates them to ``IsActive = false`` so that only a single
    active session is maintained at a time.

    Returns:
        flask.Response: A JSON response indicating the outcome of the login
        and session-deactivation operation.
    """
    body = request.get_json(silent=True) or {}
    officer_id = body.get("officer_id") or body.get("officerId")

    if not officer_id:
        return (
            jsonify({"success": False, "message": "officer_id is required."}),
            400,
        )

    try:
        zcql = get_zcql_service()
    except RuntimeError as exc:
        logger.exception("ZCQL service unavailable: %s", exc)
        return jsonify({"success": False, "message": "Service unavailable."}), 503

    # Find existing active sessions for the officer.
    select_query = (
        "SELECT ROWID, OfficerID, IsActive FROM ActiveSessions "
        "WHERE OfficerID = {oid} AND IsActive = true"
    ).format(oid=escape_zcql_string(officer_id))

    try:
        select_result = zcql.execute_query(select_query)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Failed to query ActiveSessions: %s", exc)
        return jsonify({"success": False, "message": "Failed to query sessions."}), 500

    active_sessions = []
    if select_result:
        # ZCQL returns a list of dicts, each keyed by the table name.
        for row in select_result:
            active_sessions.append(row.get("ActiveSessions", row))

    deactivated = 0
    for session in active_sessions:
        row_id = session.get("ROWID")
        if row_id is None:
            continue
        update_query = (
            "UPDATE ActiveSessions SET IsActive = false WHERE ROWID = {row_id}"
        ).format(row_id=row_id)
        try:
            zcql.execute_query(update_query)
            deactivated += 1
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception("Failed to deactivate session ROWID=%s: %s", row_id, exc)

    return (
        jsonify(
            {
                "success": True,
                "message": "Login successful. Prior active sessions deactivated.",
                "officer_id": officer_id,
                "deactivated_sessions": deactivated,
            }
        ),
        200,
    )
