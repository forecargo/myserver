import datetime
import json
import pathlib
from contextlib import asynccontextmanager
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from collector import collect_and_process
from database import get_session, init_db
from line_handler import LINE_NOTIFICATION_TARGETS, handle_text_event, notify_new_incidents, verify_signature
from models import Incident, IncidentResponse, IncidentUpdate, SummaryItem, SyncResult
from scheduler import start_scheduler, stop_scheduler


def sync_and_notify() -> dict:
    result = collect_and_process()
    if result["new_incident_ids"] and LINE_NOTIFICATION_TARGETS:
        try:
            notify_new_incidents(result["new_incident_ids"])
        except Exception as e:
            print(f"LINE notify error: {e}")
    return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler(sync_and_notify)
    yield
    stop_scheduler()


app = FastAPI(title="Trouble API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    with get_session() as session:
        yield session


DBSession = Annotated[Session, Depends(get_db)]


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui():
    html = (pathlib.Path(__file__).parent / "static" / "index.html").read_text()
    return HTMLResponse(content=html)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/incidents", response_model=list[IncidentResponse])
def list_incidents(
    db: DBSession,
    system_name: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(Incident)
    if system_name:
        stmt = stmt.where(Incident.system_name.contains(system_name))
    if status:
        stmt = stmt.where(Incident.status == status)
    if from_date:
        stmt = stmt.where(Incident.email_received_at >= from_date)
    if to_date:
        stmt = stmt.where(Incident.email_received_at <= to_date)
    stmt = stmt.order_by(Incident.email_received_at.desc()).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


@app.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: DBSession):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.put("/incidents/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: int, update: IncidentUpdate, db: DBSession):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    db.commit()
    db.refresh(incident)
    return incident


@app.delete("/incidents/{incident_id}", status_code=204)
def delete_incident(incident_id: int, db: DBSession):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    db.delete(incident)
    db.commit()


@app.post("/sync", response_model=SyncResult)
def trigger_sync():
    try:
        result = sync_and_notify()
        return SyncResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("X-Line-Signature", "")
    if not verify_signature(body, sig):
        raise HTTPException(status_code=400, detail="Invalid signature")
    payload = json.loads(body)
    for event in payload.get("events", []):
        if event.get("type") == "message" and event["message"]["type"] == "text":
            handle_text_event(event["message"]["text"], event["replyToken"])
    return {"status": "ok"}


@app.get("/summary", response_model=list[SummaryItem])
def get_summary(db: DBSession):
    stmt = (
        select(
            Incident.system_name,
            Incident.status,
            func.count(Incident.id).label("count"),
        )
        .group_by(Incident.system_name, Incident.status)
        .order_by(Incident.system_name)
    )
    rows = db.execute(stmt).all()
    return [SummaryItem(system_name=r.system_name, status=r.status, count=r.count) for r in rows]
