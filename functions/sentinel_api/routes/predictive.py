"""Predictive-analysis routes for the Sentinel-KSP API.

Provides the ``predictive_bp`` blueprint exposing endpoints that compute
crime-risk scores for a given district based on historical case volume.
"""

import logging

from flask import Blueprint, jsonify, request

from config import escape_zcql_string, get_zcql_service

logger = logging.getLogger(__name__)

predictive_bp = Blueprint("predictive_bp", __name__, url_prefix="/api/predictive")

# Thresholds used to translate the raw case count into a 0-100 risk score.
# A district with ``MAX_CASES`` or more cases maps to the maximum score (100).
MAX_CASES = 1000


def _classify_risk(score):
    """Map a numeric risk score to a categorical risk level.

    Args:
        score (int): A risk score in the range 0-100.

    Returns:
        str: ``"HIGH"``, ``"MEDIUM"`` or ``"LOW"``.
    """
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


@predictive_bp.route("/risk-score", methods=["POST"])
def risk_score():
    """Compute a 0-100 crime risk score for a district.

    Reads ``district`` from the JSON request body, counts the number of cases
    recorded for that district in ``CaseMaster`` via ZCQL, scales the count
    into a 0-100 score, and assigns a categorical risk level (``HIGH``,
    ``MEDIUM`` or ``LOW``).

    Returns:
        flask.Response: A JSON object containing the district, case count,
        computed ``risk_score`` and ``risk_level``.
    """
    body = request.get_json(silent=True) or {}
    district = body.get("district")

    if not district:
        return jsonify({"success": False, "message": "district is required."}), 400

    try:
        zcql = get_zcql_service()
    except RuntimeError as exc:
        logger.exception("ZCQL service unavailable: %s", exc)
        return jsonify({"success": False, "message": "Service unavailable."}), 503

    query = (
        "SELECT COUNT(ROWID) AS CaseCount FROM CaseMaster "
        "WHERE District = {district}"
    ).format(district=escape_zcql_string(district))

    try:
        result = zcql.execute_query(query)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Failed to query CaseMaster count: %s", exc)
        return (
            jsonify({"success": False, "message": "Failed to compute risk score."}),
            500,
        )

    case_count = 0
    if result:
        row = result[0]
        count_row = row.get("CaseMaster", row)
        try:
            case_count = int(count_row.get("CaseCount") or 0)
        except (TypeError, ValueError):
            case_count = 0

    # Scale the case count into a 0-100 risk score.
    risk_score = (
        min(100, int(round((case_count / MAX_CASES) * 100))) if MAX_CASES else 0
    )
    risk_level = _classify_risk(risk_score)

    return (
        jsonify(
            {
                "success": True,
                "district": district,
                "case_count": case_count,
                "risk_score": risk_score,
                "risk_level": risk_level,
            }
        ),
        200,
    )
