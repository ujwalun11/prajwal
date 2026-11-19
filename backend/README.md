# Person A — Engine API

## Run locally

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Open http://localhost:8000/docs and GET /api/health. SQLite is created under backend/data by default; set TRANA_DATA_DIR to change it.

## Test

```powershell
pytest backend/tests -q
```

## Notes

- Event rows are append-only and event IDs are unique/idempotent.
- Current state is derived from stored events.
- Thresholds/weights/timeouts and join codes are kept in backend/app/settings.py.
- The initial implementation does not yet load the supplied JSON Schema contract file: the repository's uploaded contract bundle must be extracted under /contracts unchanged. Until then Pydantic enforces the event envelope and type list. This is tracked as a contract-integration TODO.
- Never use this demo as an actual emergency dispatch system.
