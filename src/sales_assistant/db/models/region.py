# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.region.
"""
from sqlalchemy.orm import Mapped, mapped_column
from sales_assistant.db.base import Base, UUIDPK

class Region(Base):
    __tablename__ = "regions"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str | None]