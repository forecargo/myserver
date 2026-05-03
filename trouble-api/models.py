import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    system_name: Mapped[str] = mapped_column(String(200), index=True)
    failure_type: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), index=True, default="発生中")
    occurred_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    email_received_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    email_message_id: Mapped[str] = mapped_column(String(500), unique=True)
    raw_email_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    processed_emails: Mapped[list["ProcessedEmail"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )


class ProcessedEmail(Base):
    __tablename__ = "processed_emails"

    message_id: Mapped[str] = mapped_column(String(500), primary_key=True)
    incident_id: Mapped[int] = mapped_column(Integer, ForeignKey("incidents.id"))
    processed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident: Mapped["Incident"] = relationship(back_populates="processed_emails")


# Pydantic schemas

class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    system_name: str
    failure_type: Optional[str]
    status: str
    occurred_at: Optional[datetime.datetime]
    closed_at: Optional[datetime.datetime]
    description: Optional[str]
    response: Optional[str]
    email_subject: Optional[str]
    email_received_at: datetime.datetime
    email_message_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class IncidentUpdate(BaseModel):
    system_name: Optional[str] = None
    failure_type: Optional[str] = None
    status: Optional[str] = None
    occurred_at: Optional[datetime.datetime] = None
    closed_at: Optional[datetime.datetime] = None
    description: Optional[str] = None
    response: Optional[str] = None


class SummaryItem(BaseModel):
    system_name: str
    status: str
    count: int


class SyncResult(BaseModel):
    new_incidents: int
    updated_incidents: int
    skipped: int
    errors: list[str]
    new_incident_ids: list[int] = []
