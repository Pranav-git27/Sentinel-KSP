# Sentinel-Audit API

> DevSecOps & Spatial Intelligence Engine for Crime Analytics

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-API-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Zoho Catalyst](https://img.shields.io/badge/Zoho-Catalyst-1F73C4?logo=zoho&logoColor=white)](https://www.zoho.com/catalyst/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)

Sentinel-Audit API is a Flask backend for crime analytics on Zoho Catalyst. It reads operational crime data from Zoho Catalyst Data Store, transforms it into geospatial and graph-ready structures, and exposes focused intelligence endpoints for hotspot detection, entity-link analysis, and Modus Operandi similarity analysis.

## Architecture Overview

The backend entry point is [functions/sentinel_api/main.py](functions/sentinel_api/main.py). It creates the Flask application, enables CORS, registers the API blueprints, and exposes health probes for local execution and Zoho Catalyst Advanced Function runtime execution.

```text
Client / Analyst Tool
        |
        | HTTP JSON
        v
Flask API: functions/sentinel_api/main.py
        |
        | registered blueprints under /api
        v
Analytics Routes
  - Spatial hotspot detection
  - Case-to-accused graph construction
  - Modus Operandi text similarity
        |
        | direct REST ZCQL fetch_all_rows()
        v
Zoho Catalyst BaaS Data Store
```

Core processing flow:

| Layer | Implementation | Role |
| --- | --- | --- |
| Application factory | [functions/sentinel_api/main.py](functions/sentinel_api/main.py) | Builds the Flask app and registers route blueprints. |
| Catalyst configuration | [functions/sentinel_api/config.py](functions/sentinel_api/config.py) | Initializes the Catalyst SDK for compatibility and provides REST-backed data fetching. |
| Spatial analytics | [functions/sentinel_api/routes/geospatial.py](functions/sentinel_api/routes/geospatial.py) | Fetches `CaseMaster` rows and applies DBSCAN clustering to latitude/longitude coordinates. |
| Link analysis | [functions/sentinel_api/routes/link_analysis.py](functions/sentinel_api/routes/link_analysis.py) | Builds a NetworkX graph from `CaseMaster` and `Accused` records. |
| Predictive analytics | [functions/sentinel_api/routes/predictive.py](functions/sentinel_api/routes/predictive.py) | Computes Modus Operandi similarity using TF-IDF vectors and cosine similarity. |

### Data Processing

Spatial intelligence is implemented in [functions/sentinel_api/routes/geospatial.py](functions/sentinel_api/routes/geospatial.py). The `/api/spatial/hotspots` endpoint loads `CaseMaster` records, filters rows with usable `Latitude` and `Longitude`, converts coordinates to radians, and runs DBSCAN with a haversine distance metric. The response is returned as a GeoJSON `FeatureCollection` with hotspot membership and cluster metadata embedded in feature properties.

Entity-link intelligence is implemented in [functions/sentinel_api/routes/link_analysis.py](functions/sentinel_api/routes/link_analysis.py). The `/api/graph/network` endpoint loads `CaseMaster` and `Accused` records, creates Case and Accused nodes, connects related entities with `LINKED_TO` edges, and computes betweenness centrality to identify high-importance hubs in the network.

MO similarity analytics are implemented in [functions/sentinel_api/routes/predictive.py](functions/sentinel_api/routes/predictive.py). The `/api/analytics/mo-clusters` endpoint loads `CaseMaster` records with `ModusOperandi` text, vectorizes the corpus with TF-IDF, computes cosine similarity between case vectors, and returns matched case pairs above the requested threshold.

## Quickstart

### 1. Environment Setup

Create a `.env` file at the repository root with the Catalyst and OAuth credentials used by the backend:

```env
CATALYST_PROJECT_ID=your_project_id
CATALYST_PROJECT_KEY=your_project_key
ZC_SDK_CLIENT_ID=your_self_client_id
ZC_SDK_CLIENT_SECRET=your_self_client_secret
ZC_SDK_REFRESH_TOKEN=your_self_client_refresh_token
CATALYST_ENV=Development
```

Required variables:

| Variable | Purpose |
| --- | --- |
| `CATALYST_PROJECT_ID` | Zoho Catalyst project ID used to build BaaS REST query URLs. |
| `CATALYST_PROJECT_KEY` | Catalyst project key used by the SDK initialization path. |
| `ZC_SDK_CLIENT_ID` | Zoho OAuth self-client ID. |
| `ZC_SDK_CLIENT_SECRET` | Zoho OAuth self-client secret. |
| `ZC_SDK_REFRESH_TOKEN` | Refresh token used to generate short-lived OAuth access tokens. |
| `CATALYST_ENV` | Catalyst environment header, usually `Development` locally. |

### 2. Install Dependencies

Install the Python dependencies listed in [requirements.txt](requirements.txt):

```bash
pip install -r requirements.txt
```

The backend depends on Flask, Flask-CORS, Requests, python-dotenv, zcatalyst-sdk, NumPy, NetworkX, Pandas, and Scikit-Learn.

### 3. Run the API Server

Start the Flask application from the repository root:

```bash
python functions/sentinel_api/main.py
```

The local server binds to `http://localhost:5000` by default.

Health endpoints exposed by [functions/sentinel_api/main.py](functions/sentinel_api/main.py):

| Method | Route | Description |
| --- | --- | --- |
| GET | `/` | Base liveness probe. |
| GET | `/api/health` | Backward-compatible liveness probe. |

## API Endpoints

The following routes are verified in the registered Flask blueprints.

### GET /api/spatial/hotspots

Returns a GeoJSON `FeatureCollection` containing geocoded case points from `CaseMaster`. Each feature includes the original case fields plus hotspot annotations.

Implemented in [functions/sentinel_api/routes/geospatial.py](functions/sentinel_api/routes/geospatial.py).

Response shape:

```json
{
  "success": true,
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [77.5946, 12.9716]
      },
      "properties": {
        "CaseID": "CASE-001",
        "Latitude": 12.9716,
        "Longitude": 77.5946,
        "is_hotspot": true,
        "cluster_id": 0
      }
    }
  ],
  "summary": {
    "total_cases": 100,
    "geocoded_cases": 95,
    "hotspot_cases": 18,
    "clusters": 3,
    "eps_km": 2.0,
    "min_samples": 3
  }
}
```

### GET /api/graph/network

Returns graph visualization data built from `CaseMaster` and `Accused` records. Nodes represent Cases and Accused entities. Edges use the `LINKED_TO` relationship.

Implemented in [functions/sentinel_api/routes/link_analysis.py](functions/sentinel_api/routes/link_analysis.py).

Response shape:

```json
{
  "success": true,
  "nodes": [
    {
      "id": "case_CASE-001",
      "type": "Case",
      "label": "FIR-001",
      "case_id": "CASE-001",
      "betweenness_centrality": 0.125
    },
    {
      "id": "accused_ACC-001",
      "type": "Accused",
      "label": "Accused Name",
      "accused_id": "ACC-001",
      "betweenness_centrality": 0.0
    }
  ],
  "edges": [
    {
      "source": "accused_ACC-001",
      "target": "case_CASE-001",
      "type": "LINKED_TO",
      "relationship": "LINKED_TO"
    }
  ],
  "summary": {
    "case_nodes": 1,
    "accused_nodes": 1,
    "edge_count": 1,
    "connected_components": 1,
    "top_hubs": []
  }
}
```

### GET /api/analytics/mo-clusters

Returns pairwise Modus Operandi similarity matches from `CaseMaster`. The endpoint vectorizes `ModusOperandi` text with TF-IDF and computes cosine similarity between cases.

Implemented in [functions/sentinel_api/routes/predictive.py](functions/sentinel_api/routes/predictive.py).

Query parameters:

| Parameter | Default | Description |
| --- | --- | --- |
| `threshold` | `0.35` | Minimum cosine similarity score to include a case pair. Must be between `0` and `1`. |

Response shape:

```json
{
  "success": true,
  "threshold": 0.35,
  "pairs": [
    {
      "case_a": {
        "case_id": "CASE-001",
        "row_id": "1001",
        "fir_number": "FIR-001",
        "crime_group": "Theft",
        "crime_head": "Burglary",
        "offense_date": "2024-01-15",
        "modus_operandi": "Entry through rear door at night"
      },
      "case_b": {
        "case_id": "CASE-002",
        "row_id": "1002",
        "fir_number": "FIR-002",
        "crime_group": "Theft",
        "crime_head": "Burglary",
        "offense_date": "2024-02-10",
        "modus_operandi": "Night entry through rear entrance"
      },
      "similarity": 0.782441
    }
  ],
  "summary": {
    "total_cases": 100,
    "analyzable_cases": 72,
    "matched_pairs": 8
  }
}
```

## Data Backend

The analytics endpoints use `fetch_all_rows()` in [functions/sentinel_api/config.py](functions/sentinel_api/config.py) to query Zoho Catalyst Data Store through the Catalyst BaaS REST API instead of relying on the SDK ZCQL executor.

This REST bypass generates a fresh Zoho OAuth access token from `ZC_SDK_CLIENT_ID`, `ZC_SDK_CLIENT_SECRET`, and `ZC_SDK_REFRESH_TOKEN`, caches it in memory with an expiry safety window, and posts ZCQL payloads directly to:

```text
https://api.catalyst.zoho.in/baas/v1/project/{project_id}/query
```

The request includes:

```json
{
  "Authorization": "Zoho-oauthtoken <access_token>",
  "Environment": "Development",
  "Content-Type": "application/json"
}
```

This bypass avoids the SDK URL construction issue where ZCQL requests can be routed to `/query` without the required `/baas/v1/project/{project_id}` prefix during local execution.

The existing SDK initialization path remains available in [functions/sentinel_api/config.py](functions/sentinel_api/config.py) for non-ZCQL compatibility and cloud runtime fallback behavior.

## Repository Layout

```text
sentinel-ksp/
├── catalyst.json
├── requirements.txt
├── README.md
├── client/
│   ├── package.json
│   └── src/
└── functions/
    └── sentinel_api/
        ├── __init__.py
        ├── catalyst-config.json
        ├── config.py
        ├── main.py
        ├── routes/
        │   ├── __init__.py
        │   ├── auth.py
        │   ├── geospatial.py
        │   ├── link_analysis.py
        │   └── predictive.py
        └── scripts/
            └── seed_data.py
```

## Implementation Notes

- Flask app creation and blueprint registration live in [functions/sentinel_api/main.py](functions/sentinel_api/main.py).
- REST-backed Catalyst ZCQL row fetching lives in [functions/sentinel_api/config.py](functions/sentinel_api/config.py).
- DBSCAN hotspot clustering uses `sklearn.cluster.DBSCAN` with haversine distance over latitude/longitude coordinates.
- Entity graph generation uses NetworkX and returns frontend-ready `nodes` and `edges` arrays.
- MO clustering uses `TfidfVectorizer` and `cosine_similarity` from Scikit-Learn.
