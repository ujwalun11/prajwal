"""TRANA FastAPI backend. Run: uvicorn backend.app.main:app --reload."""
import asyncio, json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from .db import SessionLocal, EventRow, append_event, list_events
from .engine import derive_state, build_tasks, recommend
from .settings import JOIN_CODES, PHOTO_DIR

EVENT_TYPES = {"site_registered","camp_status","stock_report","shortage_request","road_status","water_level",
 "landslide_risk","team_dispatch","task_accepted","verification_report","delivery_update","decision","volunteer_location"}
app = FastAPI(title="TRANA API", version="1.0.0", description="Offline-first, trust-aware disaster relief demonstrator")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173","http://localhost:5174","http://127.0.0.1:5173","http://127.0.0.1:5174"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    type: str
    subject: str
    payload: dict = Field(default_factory=dict)
    severity: Literal["info","warning","critical"] = "info"
    source: Literal["volunteer","camp_lead","citizen","simulated_sensor","system","coordinator"]
    author_id: str
    device_time: str
    verified_by: str | None = None
    location: dict | None = None
    schema_version: Literal["1"] = "1"

class SyncIn(BaseModel):
    device_id: str
    user_id: str
    last_cursor: str = "0"
    events: list[EventIn] = Field(default_factory=list)

class JoinIn(BaseModel):
    code: str

class ApproveIn(BaseModel):
    plan_id: str
    state_version: str
    approved_by: str
    reasons: list[str] = Field(default_factory=list)

def _all(session):
    return list_events(session, since=0, limit=10000)

def _state(session):
    return derive_state(_all(session))

def _version(session):
    last = session.scalar(select(EventRow).order_by(EventRow.seq.desc()))
    return f"sv-{(last.seq if last else 0):04d}"

def _event(subject, typ, payload, source, author, severity="info"):
    return {"id": str(uuid.uuid4()), "type": typ, "subject": subject, "payload": payload, "severity": severity,
            "source": source, "author_id": author, "device_time": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
            "verified_by": None, "schema_version": "1"}

def _validate_subject(event, state, known_tasks, known_allocations, known_plans):
    typ, subject, p = event.type, event.subject, event.payload
    repeat = {"camp_status":"camp_id","shortage_request":"camp_id","verification_report":"camp_id",
              "road_status":"road_id","water_level":"sector_id","landslide_risk":"sector_id",
              "team_dispatch":"sector_id","task_accepted":"task_id","delivery_update":"allocation_id","decision":"plan_id"}
    key = repeat.get(typ)
    if key and p.get(key) != subject:
        return "invalid_schema"
    if typ == "site_registered": return None
    if typ in {"camp_status","shortage_request","verification_report"} and subject not in state["camps"]:
        return "unknown_subject"
    if typ == "stock_report" and subject not in state["camps"] and subject not in state["depots"]:
        return "unknown_subject"
    if typ == "task_accepted" and subject not in known_tasks: return "unknown_subject"
    if typ == "verification_report" and p.get("task_id") not in known_tasks: return "unknown_subject"
    if typ == "delivery_update" and subject not in known_allocations: return "unknown_subject"
    if typ == "decision" and subject not in known_plans: return "unknown_subject"
    if typ == "volunteer_location" and subject != event.author_id: return "invalid_schema"
    return None

@app.get("/api/health")
def health():
    return {"ok": True, "service": "trana-api", "version": "1.0.0"}

@app.post("/api/join")
def join(body: JoinIn):
    result = JOIN_CODES.get(body.code)
    if not result: raise HTTPException(404, detail={"code":"invalid_join_code","message":"Join code not recognised"})
    return result

@app.post("/api/sync")
def sync(body: SyncIn):
    accepted, rejected = [], []
    with SessionLocal() as session:
        before = _state(session)
        plan = recommend(before, _version(session))
        known_tasks = {t["task_id"] for t in build_tasks(before)}
        known_allocations = {a["allocation_id"] for a in plan["allocations"]}
        known_plans = {plan["plan_id"]}
        for incoming in body.events:
            if incoming.type not in EVENT_TYPES:
                rejected.append({"id":incoming.id,"code":"invalid_schema","message":"Unknown event type"})
                continue
            err = _validate_subject(incoming, before, known_tasks, known_allocations, known_plans)
            if err:
                rejected.append({"id":incoming.id,"code":err,"message":"Event failed subject validation"})
                continue
            if incoming.author_id != body.user_id and body.device_id != "dashboard":
                rejected.append({"id":incoming.id,"code":"author_mismatch","message":"Event author must match joined user"})
                continue
            row, created = append_event(session, incoming.model_dump())
            if created:
                accepted.append(incoming.id)
                before = _state(session)
            else:
                accepted.append(incoming.id)
        session.commit()
        try: cursor = int(body.last_cursor)
        except ValueError: cursor = 0
        new_events = list_events(session, since=cursor, limit=500)
        state = _state(session)
        tasks = [t for t in build_tasks(state) if t.get("assigned_to") in (None, body.user_id)]
        return {"accepted":accepted,"rejected":rejected,"new_events":new_events,"tasks":tasks,
                "cursor":str(new_events[-1]["seq"] if new_events else cursor),"has_more":len(new_events)==500,
                "server_time":datetime.now(timezone.utc).isoformat().replace("+00:00","Z")}

@app.put("/api/photos/{photo_id}")
async def put_photo(photo_id: str, file: UploadFile = File(...)):
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "upload.bin").suffix[:10]
    target = PHOTO_DIR / (photo_id + suffix)
    if not target.exists():
        data = await file.read()
        if len(data) > 8 * 1024 * 1024: raise HTTPException(413, "Photo exceeds 8 MB")
        target.write_bytes(data)
    return {"photo_id":photo_id,"stored":True}

@app.get("/api/photos/{photo_id}")
def get_photo(photo_id: str):
    matches = list(PHOTO_DIR.glob(photo_id + ".*")) if PHOTO_DIR.exists() else []
    if not matches: raise HTTPException(404,"photo_not_found")
    return FileResponse(matches[0])

@app.get("/api/state/camps")
def state_camps():
    with SessionLocal() as s:
        st = _state(s)
        return {"as_of":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"state_version":_version(s),
                "camps":list(st["camps"].values())}

@app.get("/api/state/depots")
def state_depots():
    with SessionLocal() as s:
        return {"as_of":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"state_version":_version(s),
                "depots":list(_state(s)["depots"].values())}

@app.get("/api/state/roads")
def state_roads():
    with SessionLocal() as s: return {"as_of":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"roads":list(_state(s)["roads"].values())}

@app.get("/api/state/events")
def state_events(since: int = 0, limit: int = Query(200, ge=1, le=1000)):
    with SessionLocal() as s:
        items = list_events(s, since=since, limit=limit)
        return {"events":items,"cursor":str(items[-1]["seq"] if items else since),"has_more":len(items)==limit}

@app.get("/api/tasks")
def get_tasks(assignee: str | None = None, status: str | None = None):
    with SessionLocal() as s:
        tasks = build_tasks(_state(s))
        if assignee: tasks = [t for t in tasks if t.get("assigned_to") == assignee]
        if status: tasks = [t for t in tasks if t.get("status") == status]
        return tasks

@app.get("/api/plan")
def get_plan():
    with SessionLocal() as s: return recommend(_state(s), _version(s))

@app.post("/api/plan/approve")
def approve_plan(body: ApproveIn):
    with SessionLocal() as s:
        version = _version(s)
        if body.state_version != version:
            raise HTTPException(409, detail={"code":"plan_out_of_date","message":"Inputs changed; refresh the plan","state_version":version})
        plan = recommend(_state(s), version)
        if body.plan_id != plan["plan_id"]:
            raise HTTPException(409, detail={"code":"plan_out_of_date","message":"Plan ID is no longer current","state_version":version})
        decision = _event(body.plan_id,"decision",{"plan_id":body.plan_id,"action":"approved","reasons":body.reasons,"approved_by":body.approved_by},"coordinator",body.approved_by)
        decision_row,_ = append_event(s,decision)
        delivery_events=[]
        for a in plan["allocations"]:
            e=_event(a["allocation_id"],"delivery_update",{"allocation_id":a["allocation_id"],"camp_id":a["camp_id"],
                  "item":a["item"],"quantity":a["quantity"],"status":"assigned"},"system","system")
            row,_=append_event(s,e); delivery_events.append(row)
        s.commit()
        return {"decision_event":decision_row,"delivery_events":delivery_events}

@app.get("/api/stream")
async def stream():
    async def events():
        last = 0
        while True:
            with SessionLocal() as s:
                rows = list_events(s, since=last, limit=100)
            for e in rows:
                last = e["seq"]
                yield "id: %s\nevent: trana-event\ndata: %s\n\n" % (last, json.dumps(e))
            await asyncio.sleep(1)
    return StreamingResponse(events(),media_type="text/event-stream")

@app.get("/")
def root():
    return {"name":"TRANA API","docs":"/docs","health":"/api/health"}
