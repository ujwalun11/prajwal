# TRANA architecture

TRANA is an offline-first, trust-aware disaster relief allocation demonstrator. It uses a rule-based, auditable decision path. It is not an automated dispatch system.

## System flow

1. Field staff join once while connected. Their device keeps a local session.
2. Reports are written to a Dexie/IndexedDB outbox immediately; sync is batched when online.
3. FastAPI validates each event and appends it to SQLite. Event UUIDs are idempotency keys. Server sequence numbers provide a stable cursor.
4. State is rebuilt from append-only events. Trust combines source reliability, freshness and corroboration. Silent camps become uncertain, never implicitly low priority.
5. The planner creates a two-phase allocation recommendation: a one-day minimum guarantee, then additional need-weighted allocation bounded by available stock.
6. A coordinator reviews and approves a plan. Approval checks its state version and rejects stale plans with HTTP 409.
7. Verification tasks are assigned to the nearest volunteer with a fresh location. Verification outcomes are new events.
8. Routing removes confidently closed roads and warns on uncertain closures. Insights compare TRANA to a request-count baseline.

## Approved technology

- Backend: Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLite, SQLAlchemy, NetworkX, APScheduler, SSE, ReportLab, Pytest.
- Field and dashboard: React, Vite, Tailwind, MapLibre GL JS, PMTiles, Workbox via vite-plugin-pwa, Dexie/IndexedDB, Recharts.
- Scenario: simulated JSON and GeoJSON, replay through the public sync API.
- No cloud service is required. Photos and SQLite stay on local disk.

## Data and safety rules

- Event records are append-only; corrections are new events.
- All demo numbers live in backend/app/settings.py.
- All scenario content is simulated and must be labelled.
- Keep only aggregated vulnerability counts (elderly, children, medical); never store names or individual beneficiary records.
- Every screen that shows derived data must show its "as of" timestamp.
- Recommendations are explainable and require coordinator approval. Never auto-dispatch.
- Photo files are local, git-ignored and must not contain faces.

## Scope by feature branch

- a/engine: backend ingestion, event store, sync, state, trust, task generation, priority and allocation.
- b/field: offline-first PWA, local reports/photos/outbox, task acceptance and verification.
- c/command: dashboard, simulated replay, routing, scenario, insights, what-if and report export.

The feature branches are intentionally independent and are proposed to merge into main by reviewed PRs. No feature branch is auto-merged.
