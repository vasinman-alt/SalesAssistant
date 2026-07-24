# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.mixins.

Примеси для моделей SQLAlchemy: поля синхронизации.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

class SyncFieldsMixin:
    """Добавляет поля updated_at, origin_node, version для синхронизации P2P."""
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    origin_node: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)