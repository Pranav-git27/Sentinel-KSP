# Sentinel-KSP

> A full-stack application built on **Zoho Catalyst**, combining a **React 19** web client with a **Python / Flask** serverless backend enriched with data-science capabilities (NetworkX, Pandas, scikit-learn).

[![Catalyst](https://img.shields.io/badge/Zoho-Catalyst-1f73c4?logo=zoho&logoColor=white)](https://www.zoho.com/catalyst/)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-API-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

---

## Table of Contents

- [Overview](#overview)
- [Project Architecture](#project-architecture)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Backend Setup (Python)](#2-backend-setup-python)
  - [3. Frontend Setup (React)](#3-frontend-setup-react)
- [Available Scripts](#available-scripts)
  - [Client Scripts](#client-scripts)
- [Environment Configuration](#environment-configuration)
- [Deployment](#deployment)
- [Code Analysis (Graphify)](#code-analysis-graphify)
- [Project Status](#project-status)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Sentinel-KSP** is a serverless-first application scaffolded with the Zoho Catalyst CLI. It is organized as a monorepo containing two primary modules:

1. **`client/`** — A React 19 single-page application (bootstrapped with Create React App) that serves as the user-facing frontend.
2. **`functions/`** — A Python serverless functions directory (target: `sentinel_api`) that exposes backend APIs, backed by Flask and a data-science stack for graph and ML workloads.

The project is wired to a Catalyst project named **Sentinel-KSP** in the **Development** environment (timezone: Asia/Kolkata).

---

## Project Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Browser (User)                       │
└────────────────────────────┬─────────────────────────────┘
                             │ HTTPS
                             ▼
┌──────────────────────────────────────────────────────────┐
│            Zoho Catalyst — Development Env                │
│  ┌──────────────────────┐    ┌─────────────────────────┐  │
│  │   client/ (React 19)  │    │  functions/ (Python)    │  │
│  │   Static Web Hosting  │───▶│  sentinel_api target    │  │
│  │   CRA + web-vitals    │    │  Flask + CORS            │  │
│  └──────────────────────┘    │  networkx / pandas /     │  │
│                              │  scikit-learn             │  │
│                              └─────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

The frontend is served as a static web app and communicates with the serverless Python functions hosted on Catalyst. The backend leverages graph and machine-learning libraries to power analytical endpoints.

---

## Repository Structure

```
sentinel-ksp/
├── .catalystrc              # Catalyst CLI local config (project & env IDs)
├── .graphifyignore          # Ignore rules for the Graphify analyzer
├── .gitignore               # Root ignore rules (Python, Node, OS, IDE)
├── catalyst.json            # Catalyst project wiring (functions + client)
├── requirements.txt         # Python dependencies for the functions
├── client/                  # React 19 frontend application
│   ├── .gitignore           # Client-specific ignore rules
│   ├── package.json         # React app dependencies & scripts
│   ├── client-package.json  # Catalyst client packaging metadata
│   ├── package-lock.json    # Locked dependency tree
│   ├── public/              # Static public assets (HTML, icons, manifest)
│   └── src/                 # React source code
│       ├── App.js           # Root application component
│       ├── App.css          # Application styles
│       ├── App.test.js      # Component tests
│       ├── index.js         # React DOM entry point
│       ├── index.css        # Global styles
│       ├── logo.svg         # Application logo
│       ├── reportWebVitals.js
│       └── setupTests.js
├── functions/               # Python serverless functions (sentinel_api)
└── graphify-out/            # Generated code-graph analysis (ignored)
    ├── .graphify_analysis.json
    ├── graph.json
    └── manifest.json
```

---

## Technology Stack

### Frontend (`client/`)
| Technology | Purpose |
|------------|---------|
| **React 19** | UI library |
| **Create React App 5** | Build tooling & zero-config setup |
| **react-scripts** | Dev server, build, and test runner |
| **web-vitals** | Performance metrics reporting |
| **zcatalyst-cli-plugin-react** | Catalyst-specific React integration |

### Backend (`functions/`)
| Technology | Purpose |
|------------|---------|
| **Flask** | Lightweight WSGI web framework for APIs |
| **Flask-CORS** | Cross-Origin Resource Sharing support |
| **ZCatalyst SDK** (`zcatalyst-sdk`) | Official Zoho Catalyst Python SDK |
| **NetworkX** | Graph & network analysis |
| **Pandas** | Data manipulation & analysis |
| **scikit-learn** | Machine learning utilities |

### Platform & Tooling
| Tool | Purpose |
|------|---------|
| **Zoho Catalyst CLI** | Project scaffolding, local dev, deployment |
| **Graphify** | Codebase graph & community analysis |
| **npm** | Frontend package management |

---

## Prerequisites

Ensure the following are installed on your machine before you begin:

- **Node.js** ≥ 18 (for the React client)
- **npm** (bundled with Node.js)
- **Python** ≥ 3.8 (for the serverless functions)
- **pip** (Python package installer)
- **Zoho Catalyst CLI** — [Installation guide](https://www.zoho.com/catalyst/help/cli/install.html)
- A Zoho Catalyst account with access to the **Sentinel-KSP** project

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url> sentinel-ksp
cd sentinel-ksp
```

### 2. Backend Setup (Python)

The Python dependencies power the serverless functions in [`functions/`](functions/).

```bash
# Create and activate a virtual environment
python -m venv .venv

# Activate it
# On Windows (cmd.exe):
.venv\Scripts\activate
# On macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Installed packages:
- `zcatalyst-sdk`
- `Flask`
- `Flask-CORS`
- `networkx`
- `pandas`
- `scikit-learn`

### 3. Frontend Setup (React)

```bash
cd client
npm install
npm start
```

The development server starts at **http://localhost:3000**. The page will hot-reload on edits, and lint errors are reported in the console.

---

## Available Scripts

### Client Scripts

Run these from the [`client/`](client/) directory:

| Command | Description |
|---------|-------------|
| `npm start` | Starts the React dev server on port 3000 with hot-reload. |
| `npm run build` | Bundles the app for production into the `build/` folder. |
| `npm test` | Launches the Jest test runner in interactive watch mode. |
| `npm run eject` | **One-way operation** — copies CRA config into the project for full control. Not recommended unless necessary. |

---

## Environment Configuration

The project is bound to a Catalyst project via [`.catalystrc`](.catalystrc):

| Property | Value |
|----------|-------|
| **Project name** | Sentinel-KSP |
| **Project ID** | `51748000000013048` |
| **Domain** | `sentinel-ksp-60079342823.development` |
| **Environment** | Development (`60079342823`) |
| **Timezone** | Asia/Kolkata |

The [`.gitignore`](.gitignore) file ensures that local credentials, virtual environments, build artifacts, and OS/IDE metadata are never committed.

> **Note:** The `.catalystrc` file is ignored by Git. Each developer must run `catalyst init` (or the equivalent CLI login) to generate their own local copy.

---

## Deployment

Deployment is handled through the Zoho Catalyst CLI, which reads the project wiring from [`catalyst.json`](catalyst.json):

```jsonc
{
  "functions": { "targets": ["sentinel_api"], "source": "functions" },
  "client":    { "source": "client", "plugin": "zcatalyst-cli-plugin-react" }
}
```

Typical deployment flow:

```bash
# From the project root
catalyst deploy
```

This deploys:
- The **client** static app to Catalyst Web Hosting.
- The **`sentinel_api`** function target from [`functions/`](functions/) to Catalyst Functions.

Refer to the [Catalyst CLI deployment documentation](https://www.zoho.com/catalyst/help/cli/deploy.html) for advanced options.

---

## Code Analysis (Graphify)

The project includes a [`.graphifyignore`](.graphifyignore) configuration and a generated [`graphify-out/`](graphify-out/) directory. Graphify analyzes the codebase to produce:

- **`graph.json`** — A dependency graph of the source modules.
- **`manifest.json`** — AST and semantic hashes per file for change detection.
- **`.graphify_analysis.json`** — Community detection, cohesion metrics, and "god" component identification.

> The `graphify-out/` directory is generated output and is excluded from version control via [`.gitignore`](.gitignore).

---

## Project Status

### Completed
- ✅ Zoho Catalyst project initialization (`.catalystrc`, `catalyst.json`)
- ✅ React 19 client scaffolded via Create React App (`client/`)
- ✅ Python backend dependency manifest defined (`requirements.txt`)
- ✅ Serverless function target `sentinel_api` configured (`functions/`)
- ✅ Graphify code-analysis tooling configured (`.graphifyignore`)
- ✅ Professional root [`.gitignore`](.gitignore) covering Python, Node, Catalyst, IDEs, and OS files
- ✅ Modular project documentation (this file)

### In Progress / Planned
- 🚧 Implementation of `sentinel_api` function handlers in [`functions/`](functions/)
- 🚧 Frontend feature development in [`client/src/`](client/src/)
- 🚧 Integration between the React client and the Flask API
- 🚧 Data-science endpoints leveraging NetworkX, Pandas, and scikit-learn

---

## Contributing

1. Create a feature branch from `main`: `git checkout -b feature/your-feature`
2. Ensure [`.gitignore`](.gitignore) rules are respected — never commit secrets, `node_modules/`, `.venv/`, or `graphify-out/`.
3. Run client tests before submitting: `cd client && npm test`
4. Write clear, conventional commit messages.
5. Open a pull request describing the change and linking any related issue.

---

## License

This project is proprietary. All rights reserved. See the project maintainers for licensing and usage terms.
