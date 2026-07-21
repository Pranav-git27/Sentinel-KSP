"""Geospatial routes for the Sentinel-KSP API.

Provides the ``geospatial_bp`` blueprint exposing endpoints that return
crime-incident data with geographic coordinates for map rendering.
"""

import logging

from flask import Blueprint, jsonify

from config import get_zcql_service

logger = logging.getLogger(__name__)

geospatial_bp = Blueprint("geospatial_bp", __name__, url_prefix="/api/geospatial")


@geospatial_bp.route("/incidents", methods=["GET"])
def get_incidents():
    """Return all crime incidents with their geospatial coordinates.

    Queries the ``CaseMaster`` table via ZCQL for the fields required to plot
    incidents on a map: ``CaseID``, ``FIRNumber``, ``CrimeGroup``,
    ``CrimeHead``, ``Latitude``, ``Longitude`` and ``OffenseDate``.

    Returns:
        flask.Response: A JSON object with a ``data`` key containing an array
        of incident objects.
    """
    query = (
        "SELECT CaseID, FIRNumber, CrimeGroup, CrimeHead, "
        "Latitude, Longitude, OffenseDate FROM CaseMaster"
    )

    try:
        zcql = get_zcql_service()
    except RuntimeError as exc:
        logger.exception("ZCQL service unavailable: %s", exc)
        return (
            jsonify({"success": False, "message": "Service unavailable.", "data": []}),
            503,
        )

    try:
        result = zcql.execute_query(query)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Failed to query CaseMaster: %s", exc)
        return (
            jsonify(
                {"success": False, "message": "Failed to fetch incidents.", "data": []}
            ),
            500,
        )

    incidents = []
    if result:
        for row in result:
            # ZCQL returns rows keyed by the table name.
            incidents.append(row.get("CaseMaster", row))

    return jsonify({"success": True, "data": incidents}), 200
