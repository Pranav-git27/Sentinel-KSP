"""Link-analysis routes for the Sentinel-KSP API.

Provides the ``link_analysis_bp`` blueprint exposing endpoints that build
relationship graphs between cases and accused persons using NetworkX.
"""

import logging

import networkx as nx
from flask import Blueprint, jsonify

from config import fetch_all_rows, get_zcql_service

logger = logging.getLogger(__name__)

link_analysis_bp = Blueprint("link_analysis_bp", __name__, url_prefix="/api")


def _normalize_rows(rows, table_name):
    """Return Catalyst/ZCQL rows as plain dictionaries."""
    normalized = []
    for row in rows or []:
        if isinstance(row, dict):
            normalized.append(row.get(table_name, row))
    return normalized


def _case_node_id(case_row):
    return "case_{}".format(case_row.get("CaseID") or case_row.get("ROWID"))


def _accused_node_id(accused_row):
    return "accused_{}".format(
        accused_row.get("AccusedID") or accused_row.get("ROWID") or accused_row.get("Name")
    )


@link_analysis_bp.route("/analysis/link-graph", methods=["GET"])
def get_link_graph():
    """Build and return a case-accused relationship graph."""
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

    cases = _normalize_rows(case_result, "CaseMaster")
    accused = _normalize_rows(accused_result, "Accused")
    graph = nx.Graph()

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
        target = case_index.get(case_id)
        if target is not None:
            graph.add_edge(node_id, target, relationship="INVOLVED_IN")

    nodes = [{"id": node_id, **data} for node_id, data in graph.nodes(data=True)]
    edges = [
        {"source": source, "target": target, **data}
        for source, target, data in graph.edges(data=True)
    ]

    return jsonify({"graph": {"nodes": nodes, "edges": edges}}), 200


@link_analysis_bp.route("/graph/network", methods=["GET"])
def get_graph_network():
    """Return a centrality-scored case-to-accused network graph."""
    try:
        cases = _normalize_rows(fetch_all_rows("CaseMaster"), "CaseMaster")
        accused = _normalize_rows(fetch_all_rows("Accused"), "Accused")
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Failed to fetch network graph source rows: %s", exc)
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Failed to build network graph.",
                    "nodes": [],
                    "edges": [],
                    "summary": {},
                }
            ),
            500,
        )

    graph = nx.Graph()
    case_index = {}

    for case_row in cases:
        case_id = case_row.get("CaseID") or case_row.get("ROWID")
        if case_id is None:
            continue
        node_id = _case_node_id(case_row)
        graph.add_node(
            node_id,
            type="Case",
            label=case_row.get("FIRNumber") or case_row.get("CaseID") or node_id,
            case_id=case_row.get("CaseID"),
            fir_number=case_row.get("FIRNumber"),
            crime_group=case_row.get("CrimeGroup"),
            crime_head=case_row.get("CrimeHead"),
            offense_date=case_row.get("OffenseDate"),
        )
        case_index[str(case_id)] = node_id

    for accused_row in accused:
        accused_id = accused_row.get("AccusedID") or accused_row.get("ROWID") or accused_row.get("Name")
        case_id = accused_row.get("CaseID")
        if accused_id is None:
            continue

        node_id = _accused_node_id(accused_row)
        graph.add_node(
            node_id,
            type="Accused",
            label=accused_row.get("Name") or accused_row.get("AccusedID") or node_id,
            accused_id=accused_row.get("AccusedID"),
            name=accused_row.get("Name"),
            arrest_status=accused_row.get("ArrestStatus"),
            case_id=case_id,
        )

        target_node_id = case_index.get(str(case_id)) if case_id is not None else None
        if target_node_id is not None:
            graph.add_edge(
                node_id,
                target_node_id,
                type="LINKED_TO",
                relationship="LINKED_TO",
            )

    centrality = nx.betweenness_centrality(graph) if graph.number_of_nodes() else {}

    nodes = []
    for node_id, data in graph.nodes(data=True):
        nodes.append(
            {
                "id": node_id,
                **data,
                "betweenness_centrality": round(centrality.get(node_id, 0.0), 6),
            }
        )

    edges = [
        {
            "source": source,
            "target": target,
            **data,
        }
        for source, target, data in graph.edges(data=True)
    ]

    ranked_hubs = sorted(
        nodes,
        key=lambda node: node["betweenness_centrality"],
        reverse=True,
    )[:10]

    return (
        jsonify(
            {
                "success": True,
                "nodes": nodes,
                "edges": edges,
                "summary": {
                    "case_nodes": sum(1 for node in nodes if node.get("type") == "Case"),
                    "accused_nodes": sum(1 for node in nodes if node.get("type") == "Accused"),
                    "edge_count": len(edges),
                    "connected_components": nx.number_connected_components(graph)
                    if graph.number_of_nodes()
                    else 0,
                    "top_hubs": ranked_hubs,
                },
            }
        ),
        200,
    )
