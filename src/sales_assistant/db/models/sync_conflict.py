# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.sync_conflict.
"""
import uuid
from datetime import datetime
from sqlalchemy import Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sales_assistant.db.base import Base, UUIDPK

class SyncConflictLog(Base):
    __tablename__ = "sync_conflict_log"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    entity_type: Mapped[str]
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    losing_version: Mapped[dict] = mapped_column(JSON)
    resolved_at: Mapped[datetime | None]
    detected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)