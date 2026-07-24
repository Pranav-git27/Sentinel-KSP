"""Geospatial routes for the Sentinel-KSP API.

Provides the ``geospatial_bp`` blueprint exposing endpoints that return
crime-incident data with geographic coordinates for map rendering.
"""

import logging
import math

import numpy as np
from flask import Blueprint, jsonify
from sklearn.cluster import DBSCAN

from config import fetch_all_rows, get_zcql_service

logger = logging.getLogger(__name__)

geospatial_bp = Blueprint("geospatial_bp", __name__, url_prefix="/api")

EARTH_RADIUS_KM = 6371.0088
DEFAULT_HOTSPOT_EPS_KM = 2.0
DEFAULT_HOTSPOT_MIN_SAMPLES = 3


def _normalize_rows(rows, table_name):
    """Return Catalyst/ZCQL rows as plain dictionaries."""
    normalized = []
    for row in rows or []:
        if isinstance(row, dict):
            normalized.append(row.get(table_name, row))
    return normalized


def _as_float(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _json_safe(value):
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _case_properties(case_row, is_hotspot, cluster_id):
    properties = {key: _json_safe(value) for key, value in case_row.items()}
    properties["is_hotspot"] = bool(is_hotspot)
    properties["cluster_id"] = None if cluster_id == -1 else int(cluster_id)
    return properties


@geospatial_bp.route("/geospatial/incidents", methods=["GET"])
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

    incidents = _normalize_rows(result, "CaseMaster")
    return jsonify({"success": True, "data": incidents}), 200


@geospatial_bp.route("/spatial/hotspots", methods=["GET"])
def get_spatial_hotspots():
    """Return CaseMaster points annotated with DBSCAN hotspot membership."""
    try:
        cases = _normalize_rows(fetch_all_rows("CaseMaster"), "CaseMaster")
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Failed to fetch CaseMaster rows for hotspots: %s", exc)
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Failed to fetch hotspot data.",
                    "type": "FeatureCollection",
                    "features": [],
                }
            ),
            500,
        )

    valid_points = []
    for index, case_row in enumerate(cases):
        latitude = _as_float(case_row.get("Latitude"))
        longitude = _as_float(case_row.get("Longitude"))
        if latitude is None or longitude is None:
            continue
        valid_points.append((index, latitude, longitude))

    labels_by_case_index = {index: -1 for index, _, _ in valid_points}
    if len(valid_points) >= DEFAULT_HOTSPOT_MIN_SAMPLES:
        coordinates_radians = np.radians(
            [[latitude, longitude] for _, latitude, longitude in valid_points]
        )
        clustering = DBSCAN(
            eps=DEFAULT_HOTSPOT_EPS_KM / EARTH_RADIUS_KM,
            min_samples=DEFAULT_HOTSPOT_MIN_SAMPLES,
            metric="haversine",
        ).fit(coordinates_radians)
        labels_by_case_index = {
            case_index: int(label)
            for (case_index, _, _), label in zip(valid_points, clustering.labels_)
        }

    features = []
    for index, case_row in enumerate(cases):
        latitude = _as_float(case_row.get("Latitude"))
        longitude = _as_float(case_row.get("Longitude"))
        if latitude is None or longitude is None:
            continue

        cluster_id = labels_by_case_index.get(index, -1)
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude],
                },
                "properties": _case_properties(
                    case_row=case_row,
                    is_hotspot=cluster_id != -1,
                    cluster_id=cluster_id,
                ),
            }
        )

    return (
        jsonify(
            {
                "success": True,
                "type": "FeatureCollection",
                "features": features,
                "summary": {
                    "total_cases": len(cases),
                    "geocoded_cases": len(features),
                    "hotspot_cases": sum(
                        1 for feature in features if feature["properties"]["is_hotspot"]
                    ),
                    "clusters": len(
                        {
                            feature["properties"]["cluster_id"]
                            for feature in features
                            if feature["properties"]["cluster_id"] is not None
                        }
                    ),
                    "eps_km": DEFAULT_HOTSPOT_EPS_KM,
                    "min_samples": DEFAULT_HOTSPOT_MIN_SAMPLES,
                },
            }
        ),
        200,
    )
