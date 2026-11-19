# TRANA — Offline-First, Trust-Aware Disaster Relief Allocation Engine

TRANA is a demo disaster-relief coordination system for field reporting, trust-aware camp status, explainable resource allocation, volunteer verification and coordinator approval.

## Team branches

| Contributor | Branch | Owned area |
|---|---|---|
| Person A | `a/engine` | FastAPI event ingestion, sync, trust, tasks, priority and allocation |
| Person B | `b/field` | Offline-first field PWA |
| Person C | `c/command` | Coordinator dashboard, routing, insights and simulated scenario |

Each feature branch is independent. Submit a pull request to `main`; do not push application work directly to `main`. The team lead reviews and merges PRs.

## Contract source

The original uploaded source bundles are stored under `source_materials/` as unmodified ZIPs. Extract the contracts bundle into the repository root so that `contracts/` exists. Do not edit contract files without explicit team approval.

## Local development

See `docs/architecture.md` and `docs/team-workflow.md`. Each feature branch contains its own run instructions. The integrated local stack uses SQLite and local filesystem storage; no cloud service is required.

All scenario data is simulated. TRANA is a hackathon demonstrator, not a life-safety certified dispatch system.
