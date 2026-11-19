# TRANA — Offline-First, Trust-Aware Disaster Relief Allocation Engine

TRANA is a deterministic, explainable disaster-relief coordination demonstrator. It accepts offline field reports, derives camp confidence, flags silent camps for verification, recommends a minimum-guarantee/priority allocation, and requires coordinator approval.

**All included scenario data is fictional and simulated.** TRANA is a hackathon prototype, not a certified emergency-response system.

## Team branches

| Contributor | Branch | Work |
|---|---|---|
| Person A | [a/engine](https://github.com/ujwalun11/prajwal/tree/a/engine) | FastAPI, append-only SQLite event store, sync, trust, tasks, priorities and allocations |
| Person B | [b/field](https://github.com/ujwalun11/prajwal/tree/b/field) | Offline-first React PWA, Dexie outbox, field reports, observations, photos and verification |
| Person C | [c/command](https://github.com/ujwalun11/prajwal/tree/c/command) | Coordinator dashboard, routing, equity insights, what-if, reports and scenario replay |

Each contributor's branch remains separate. Each branch has a pull request to `main`; **the team lead should review and merge PRs manually**. No feature branch is merged automatically.

## Local quick start

After the three PRs have been reviewed and merged into `main`:

```powershell
git clone https://github.com/ujwalun11/prajwal.git
cd prajwal
docker compose up --build
```

Open:
- API docs: http://localhost:8000/docs
- Field PWA: http://localhost:5173
- Coordinator dashboard: http://localhost:5174

In another PowerShell window, replay the fictional scenario:

```powershell
py scenario\replay.py --base-url http://localhost:8000 --speed 10
py scripts\smoke_test.py --base-url http://localhost:8000
```

The API stores events and photos on local disk under `backend/data/`. No cloud database, hosted object storage, remote compute, or map tile service is required. For a detailed offline basemap, provide a local PMTiles archive and a local MapLibre style as described in each web app README.

## Run without Docker

Backend:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Field and dashboard each have their own `npm install`, `npm run dev`, `npm test` and `npm run build` commands in their respective README files.

## Architecture and collaboration

See [docs/architecture.md](docs/architecture.md), [docs/team-workflow.md](docs/team-workflow.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Contract source status

The source contract bundle was provided separately as `contracts_v1_draft.zip`. The decisions transcribed from that file are in `contracts/DECISIONS.md`. The exact `events.schema.json`, `openapi.yaml`, and original sample files still need to be copied into `contracts/` from the supplied ZIP before declaring contract-level conformance. The common brief calls the version frozen/final while the ZIP README/OpenAPI metadata retain DRAFT labels; see `contracts/README.md`.
