"""Link-analysis routes for the Sentinel-KSP API.

Provides the ``link_analysis_bp`` blueprint exposing endpoints that build
relationship graphs between cases and accused persons using NetworkX.
"""

import logging

import networkx as nx
from flask import Blueprint, jsonify

from config import get_zcql_service

logger = logging.getLogger(__name__)

link_analysis_bp = Blueprint("link_analysis_bp", __name__, url_prefix="/api/analysis")


@link_analysis_bp.route("/link-graph", methods=["GET"])
def get_link_graph():
    """Build and return a case-accused relationship graph.

    Queries the ``CaseMaster`` and ``Accused`` tables via ZCQL and constructs
    a NetworkX graph where:

    * case nodes are identified as ``case_{ROWID}``
    * accused nodes are identified as ``accused_{ROWID}``
    * an ``INVOLVED_IN`` edge connects an accused node to the case node it is
      associated with (resolved via the ``CaseID`` column on the ``Accused``
      row matched against the ``CaseID`` of a ``CaseMaster`` row).

    Returns:
        flask.Response: A JSON object of the form
        ``{"graph": {"nodes": [...], "edges": [...]}}``.
    """
    case_query = "SELECT ROWID, CaseID, FIRNumber, CrimeGroup FROM CaseMaster"
    accused_query = "SELECT ROWID, Name, CaseID FROM Accused"

    try:
        zcql = get_zcql_service()
    except RuntimeError as exc:
        logger.exception("ZCQL service unavailable: %s", exc)
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Service unavailable.",
                    "graph": {"nodes": [], "edges": []},
                }
            ),
            503,
        )

    try:
        case_result = zcql.execute_query(case_query)
        accused_result = zcql.execute_query(accused_query)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Failed to query CaseMaster/Accused: %s", exc)
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Failed to build graph.",
                    "graph": {"nodes": [], "edges": []},
                }
            ),
            500,
        )

    cases = []
    if case_result:
        for row in case_result:
            cases.append(row.get("CaseMaster", row))

    accused = []
    if accused_result:
        for row in accused_result:
            accused.append(row.get("Accused", row))

    graph = nx.Graph()

    # Index cases by CaseID for quick edge resolution.
    case_index = {}
    for case_row in cases:
        row_id = case_row.get("ROWID")
        case_id = case_row.get("CaseID")
        if row_id is None:
            continue
        node_id = "case_{}".format(row_id)
        graph.add_node(
            node_id,
            type="case",
            case_id=case_id,
            fir_number=case_row.get("FIRNumber"),
            crime_group=case_row.get("CrimeGroup"),
        )
        if case_id is not None:
            case_index[case_id] = node_id

    for accused_row in accused:
        row_id = accused_row.get("ROWID")
        case_id = accused_row.get("CaseID")
        if row_id is None:
            continue
        node_id = "accused_{}".format(row_id)
        graph.add_node(
            node_id,
            type="accused",
            name=accused_row.get("Name"),
            case_id=case_id,
        )
        # Connect the accused to the corresponding case node.
        target = case_index.get(case_id)
        if target is not None:
            graph.add_edge(node_id, target, relationship="INVOLVED_IN")

    nodes = [{"id": node_id, **data} for node_id, data in graph.nodes(data=True)]
    edges = [
        {"source": source, "target": target, **data}
        for source, target, data in graph.edges(data=True)
    ]

    return jsonify({"graph": {"nodes": nodes, "edges": edges}}), 200
