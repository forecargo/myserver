import datetime
import json
import os
import pathlib
from contextlib import asynccontextmanager
from typing import Annotated, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

LIFF_ID = os.getenv("LIFF_ID", "")

from collector import collect_and_process
from database import get_session, init_db
from line_handler import LINE_NOTIFICATION_TARGETS, handle_text_event, is_allowed_source, notify_new_incidents, notify_resolved_incidents, notify_updated_incidents, send_sample_notification, verify_signature
from models import Incident, IncidentResponse, IncidentUpdate, LiffAccessLog, LiffAccessLogResponse, LiffAllowedUser, LiffAllowedUserCreate, LiffAllowedUserResponse, SummaryItem, SyncResult
from scheduler import start_scheduler, stop_scheduler


def sync_and_notify() -> dict:
    result = collect_and_process()
    if result["new_incident_ids"] and LINE_NOTIFICATION_TARGETS:
        try:
            notify_new_incidents(result["new_incident_ids"])
        except Exception as e:
            print(f"LINE notify error (new): {e}")
    if result.get("resolved_new_incident_ids") and LINE_NOTIFICATION_TARGETS:
        try:
            notify_resolved_incidents(result["resolved_new_incident_ids"])
        except Exception as e:
            print(f"LINE notify error (resolved): {e}")
    if result.get("status_changed_incident_ids") and LINE_NOTIFICATION_TARGETS:
        try:
            notify_updated_incidents(result["status_changed_incident_ids"])
        except Exception as e:
            print(f"LINE notify error (updated): {e}")
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


async def _verify_liff_token(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.removeprefix("Bearer ")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.line.me/v2/profile",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5.0,
        )
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid LIFF token")
    line_user_id = r.json()["userId"]
    allowed = db.execute(
        select(LiffAllowedUser).where(LiffAllowedUser.line_user_id == line_user_id)
    ).scalar_one_or_none()
    if not allowed:
        display_name = r.json().get("displayName", "")
        try:
            existing_log = db.execute(
                select(LiffAccessLog).where(LiffAccessLog.line_user_id == line_user_id)
            ).scalar_one_or_none()
            if existing_log:
                existing_log.line_display_name = display_name
                existing_log.accessed_at = datetime.datetime.now(datetime.timezone.utc)
            else:
                count = db.execute(select(func.count()).select_from(LiffAccessLog)).scalar()
                if count >= 10:
                    oldest = db.execute(
                        select(LiffAccessLog).order_by(LiffAccessLog.accessed_at.asc()).limit(1)
                    ).scalar_one_or_none()
                    if oldest:
                        db.delete(oldest)
                db.add(LiffAccessLog(line_user_id=line_user_id, line_display_name=display_name))
            db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(
            status_code=403,
            detail=f"アクセス権限がありません。管理者にLINE IDをお伝えください: {line_user_id}",
        )
    return {"line_user_id": line_user_id, "employee_code": allowed.employee_code, "name": allowed.name}


LiffUser = Annotated[dict, Depends(_verify_liff_token)]


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


@app.post("/line/test-notify")
def test_line_notify():
    sent = send_sample_notification()
    return {"sent": sent, "targets": LINE_NOTIFICATION_TARGETS}


@app.get("/liff", response_class=HTMLResponse, include_in_schema=False)
def liff_ui():
    html = (pathlib.Path(__file__).parent / "static" / "index.html").read_text()
    return HTMLResponse(content=html)


@app.get("/liff/config")
def liff_config():
    return {"liff_id": LIFF_ID}


@app.get("/liff/me")
async def liff_me(user: LiffUser) -> dict:
    return user


@app.get("/liff/summary", response_model=list[SummaryItem])
async def liff_get_summary(_: LiffUser, db: DBSession):
    stmt = (
        select(Incident.system_name, Incident.status, func.count(Incident.id).label("count"))
        .group_by(Incident.system_name, Incident.status)
        .order_by(Incident.system_name)
    )
    rows = db.execute(stmt).all()
    return [SummaryItem(system_name=r.system_name, status=r.status, count=r.count) for r in rows]


@app.get("/liff/incidents", response_model=list[IncidentResponse])
async def liff_list_incidents(
    _: LiffUser,
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


@app.get("/liff/incidents/{incident_id}", response_model=IncidentResponse)
async def liff_get_incident(incident_id: int, _: LiffUser, db: DBSession):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.put("/liff/incidents/{incident_id}", response_model=IncidentResponse)
async def liff_update_incident(incident_id: int, update: IncidentUpdate, _: LiffUser, db: DBSession):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    db.commit()
    db.refresh(incident)
    return incident


@app.get("/members", response_model=list[LiffAllowedUserResponse])
def list_members(db: DBSession):
    return db.execute(select(LiffAllowedUser).order_by(LiffAllowedUser.employee_code)).scalars().all()


@app.post("/members", response_model=LiffAllowedUserResponse, status_code=201)
def create_member(body: LiffAllowedUserCreate, db: DBSession):
    exists = db.execute(
        select(LiffAllowedUser).where(
            (LiffAllowedUser.line_user_id == body.line_user_id) |
            (LiffAllowedUser.employee_code == body.employee_code)
        )
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="行員コードまたはLINE IDが既に登録されています")
    member = LiffAllowedUser(**body.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@app.delete("/members/{member_id}", status_code=204)
def delete_member(member_id: int, db: DBSession):
    member = db.get(LiffAllowedUser, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(member)
    db.commit()


@app.get("/access-log", response_model=list[LiffAccessLogResponse])
def list_access_log(db: DBSession):
    allowed_ids = db.execute(select(LiffAllowedUser.line_user_id)).scalars().all()
    stmt = select(LiffAccessLog)
    if allowed_ids:
        stmt = stmt.where(LiffAccessLog.line_user_id.not_in(allowed_ids))
    stmt = stmt.order_by(LiffAccessLog.accessed_at.desc()).limit(10)
    return db.execute(stmt).scalars().all()


@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("X-Line-Signature", "")
    if not verify_signature(body, sig):
        raise HTTPException(status_code=400, detail="Invalid signature")
    payload = json.loads(body)
    for event in payload.get("events", []):
        print(f"LINE source: {event.get('source')}", flush=True)
        if not is_allowed_source(event):
            continue
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
