"""SQLite event store. Events are immutable; corrections are appended as new rows."""
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, Integer, String, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .settings import DATABASE_URL, DATA_DIR

DATA_DIR.mkdir(parents=True, exist_ok=True)
if DATABASE_URL.startswith("sqlite:///"):
    Path(DATABASE_URL.replace("sqlite:///", "", 1)).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class EventRow(Base):
    __tablename__ = "events"
    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(40), index=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(12))
    source: Mapped[str] = mapped_column(String(24))
    author_id: Mapped[str] = mapped_column(String(80), index=True)
    device_time: Mapped[str] = mapped_column(String(40))
    server_time: Mapped[str] = mapped_column(String(40))
    verified_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str] = mapped_column(String(4), default="1")

Base.metadata.create_all(engine)

def row_to_event(row: EventRow) -> dict:
    event = {
        "id": row.id, "type": row.type, "subject": row.subject,
        "payload": json.loads(row.payload), "severity": row.severity,
        "source": row.source, "author_id": row.author_id,
        "device_time": row.device_time, "server_time": row.server_time,
        "seq": row.seq, "verified_by": row.verified_by,
        "schema_version": row.schema_version,
    }
    if row.location:
        event["location"] = json.loads(row.location)
    return event

def list_events(session, since: int = 0, limit: int = 500) -> list[dict]:
    rows = session.scalars(select(EventRow).where(EventRow.seq > since).order_by(EventRow.seq).limit(limit)).all()
    return [row_to_event(row) for row in rows]

def append_event(session, event: dict) -> tuple[dict | None, bool]:
    existing = session.scalar(select(EventRow).where(EventRow.id == event["id"]))
    if existing:
        return row_to_event(existing), False
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    row = EventRow(
        id=event["id"], type=event["type"], subject=event["subject"],
        payload=json.dumps(event.get("payload", {}), separators=(",", ":")),
        severity=event["severity"], source=event["source"], author_id=event["author_id"],
        device_time=event["device_time"], server_time=now,
        verified_by=event.get("verified_by"),
        location=json.dumps(event["location"]) if event.get("location") else None,
        schema_version=event.get("schema_version", "1"),
    )
    session.add(row)
    session.flush()
    return row_to_event(row), True
