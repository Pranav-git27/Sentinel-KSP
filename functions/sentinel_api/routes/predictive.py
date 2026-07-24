"""Predictive-analysis routes for the Sentinel-KSP API.

Provides the ``predictive_bp`` blueprint exposing endpoints that compute
crime-risk scores for a given district based on historical case volume.
"""

import logging

from flask import Blueprint, jsonify, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import escape_zcql_string, fetch_all_rows, get_zcql_service

logger = logging.getLogger(__name__)

predictive_bp = Blueprint("predictive_bp", __name__, url_prefix="/api")

MAX_CASES = 1000
DEFAULT_MO_SIMILARITY_THRESHOLD = 0.35


def _normalize_rows(rows, table_name):
    """Return Catalyst/ZCQL rows as plain dictionaries."""
    normalized = []
    for row in rows or []:
        if isinstance(row, dict):
            normalized.append(row.get(table_name, row))
    return normalized


def _classify_risk(score):
    """Map a numeric risk score to a categorical risk level."""
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def _case_identifier(case_row):
    return case_row.get("CaseID") or case_row.get("ROWID")


def _case_summary(case_row):
    return {
        "case_id": case_row.get("CaseID"),
        "row_id": case_row.get("ROWID"),
        "fir_number": case_row.get("FIRNumber"),
        "crime_group": case_row.get("CrimeGroup"),
        "crime_head": case_row.get("CrimeHead"),
        "offense_date": case_row.get("OffenseDate"),
        "modus_operandi": case_row.get("ModusOperandi"),
    }


@predictive_bp.route("/predictive/risk-score", methods=["POST"])
def risk_score():
    """Compute a 0-100 crime risk score for a district."""
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

    risk_value = min(100, int(round((case_count / MAX_CASES) * 100))) if MAX_CASES else 0
    risk_level = _classify_risk(risk_value)

    return (
        jsonify(
            {
                "success": True,
                "district": district,
                "case_count": case_count,
                "risk_score": risk_value,
                "risk_level": risk_level,
            }
        ),
        200,
    )


@predictive_bp.route("/analytics/mo-clusters", methods=["GET"])
def get_mo_clusters():
    """Return high-similarity case pairs based on ModusOperandi text."""
    threshold_arg = request.args.get("threshold", DEFAULT_MO_SIMILARITY_THRESHOLD)
    try:
        threshold = float(threshold_arg)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "threshold must be numeric."}), 400

    if threshold < 0 or threshold > 1:
        return jsonify({"success": False, "message": "threshold must be between 0 and 1."}), 400

    try:
        cases = _normalize_rows(fetch_all_rows("CaseMaster"), "CaseMaster")
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Failed to fetch CaseMaster rows for MO clustering: %s", exc)
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Failed to compute MO clusters.",
                    "pairs": [],
                    "summary": {},
                }
            ),
            500,
        )

    analyzable_cases = [
        case_row
        for case_row in cases
        if _case_identifier(case_row) is not None
        and str(case_row.get("ModusOperandi") or "").strip()
    ]

    if len(analyzable_cases) < 2:
        return (
            jsonify(
                {
                    "success": True,
                    "threshold": threshold,
                    "pairs": [],
                    "summary": {
                        "total_cases": len(cases),
                        "analyzable_cases": len(analyzable_cases),
                        "matched_pairs": 0,
                    },
                }
            ),
            200,
        )

    corpus = [str(case_row.get("ModusOperandi") or "") for case_row in analyzable_cases]

    try:
        vectors = TfidfVectorizer(stop_words="english").fit_transform(corpus)
        similarity_matrix = cosine_similarity(vectors)
    except ValueError as exc:
        logger.exception("Failed to vectorize ModusOperandi text: %s", exc)
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Failed to vectorize ModusOperandi text.",
                    "pairs": [],
                    "summary": {},
                }
            ),
            500,
        )

    pairs = []
    for left_index in range(len(analyzable_cases)):
        for right_index in range(left_index + 1, len(analyzable_cases)):
            score = float(similarity_matrix[left_index][right_index])
            if score >= threshold:
                pairs.append(
                    {
                        "case_a": _case_summary(analyzable_cases[left_index]),
                        "case_b": _case_summary(analyzable_cases[right_index]),
                        "similarity": round(score, 6),
                    }
                )

    pairs.sort(key=lambda pair: pair["similarity"], reverse=True)

    return (
        jsonify(
            {
                "success": True,
                "threshold": threshold,
                "pairs": pairs,
                "summary": {
                    "total_cases": len(cases),
                    "analyzable_cases": len(analyzable_cases),
                    "matched_pairs": len(pairs),
                },
            }
        ),
        200,
    )
