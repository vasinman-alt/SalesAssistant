# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.activity.
"""
from sqlalchemy.orm import Mapped, mapped_column
from sales_assistant.db.base import Base, UUIDPK

class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    okved_code: Mapped[str | None]
    description: Mapped[str | None]
    industry: Mapped[str | None]