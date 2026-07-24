# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.interaction.
"""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Uuid, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sales_assistant.db.base import Base, UUIDPK

class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"))
    contact_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("contacts.id"))
    type: Mapped[str]  # call, meeting, letter, video, message, note
    event_date: Mapped[datetime]
    entry_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    subject: Mapped[str]
    description: Mapped[str | None]
    result: Mapped[str | None]
    next_action: Mapped[str | None]
    is_voided: Mapped[bool] = mapped_column(Boolean, default=False)
    voided_reason: Mapped[str | None]
    replaces_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("interactions.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    origin_node: Mapped[uuid.UUID]

    # Связи
    company: Mapped["Company"] = relationship(back_populates="interactions")
    contact: Mapped["Contact"] = relationship()
    replaces: Mapped["Interaction"] = relationship(remote_side=[id])