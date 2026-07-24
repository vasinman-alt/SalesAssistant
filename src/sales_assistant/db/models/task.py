# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.task.
"""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sales_assistant.db.base import Base, UUIDPK
from sales_assistant.db.models.mixins import SyncFieldsMixin

class Task(Base, SyncFieldsMixin):
    __tablename__ = "tasks"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("companies.id"))
    contact_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("contacts.id"))
    interaction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("interactions.id"))
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None]
    due_date: Mapped[datetime | None]
    priority: Mapped[str]  # low, medium, high
    status: Mapped[str]  # open, in_progress, done, cancelled
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    reminder_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[datetime | None]

    # Связи
    company: Mapped["Company"] = relationship(back_populates="tasks")
    contact: Mapped["Contact"] = relationship()
    interaction: Mapped["Interaction"] = relationship()
    assignee: Mapped["User"] = relationship(foreign_keys=[assignee_id])