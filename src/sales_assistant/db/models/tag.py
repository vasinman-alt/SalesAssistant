# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.tag.
"""
import uuid
from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sales_assistant.db.base import Base, UUIDPK

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    color: Mapped[str | None]


class EntityTag(Base):
    __tablename__ = "entity_tags"

    tag_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tags.id"), primary_key=True)
    entity_type: Mapped[str] = mapped_column(primary_key=True)  # 'company', 'contact', etc.
    entity_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)