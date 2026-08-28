# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.company.
"""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Uuid, JSON, Table, Column, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sales_assistant.db.base import Base, UUIDPK
from sales_assistant.db.models.mixins import SyncFieldsMixin

company_activity = Table(
    "company_activities",
    Base.metadata,
    Column("company_id", Uuid, ForeignKey("companies.id"), primary_key=True),
    Column("activity_id", Uuid, ForeignKey("activities.id"), primary_key=True),
)

class Company(Base, SyncFieldsMixin):
    __tablename__ = "companies"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    legal_name: Mapped[str | None] = mapped_column(String, nullable=True)
    inn: Mapped[str | None] = mapped_column(String, nullable=True)
    region_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("regions.id"))
    legal_address: Mapped[str | None]
    actual_address: Mapped[str | None]
    website: Mapped[str | None]
    comment: Mapped[str | None]
    source: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="active")  # active | archived
    custom_fields: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))

    # Связи
    region: Mapped["Region"] = relationship()
    activities: Mapped[list["Activity"]] = relationship(secondary=company_activity)
    contacts: Mapped[list["Contact"]] = relationship(back_populates="company")
    interactions: Mapped[list["Interaction"]] = relationship(back_populates="company")
    tasks: Mapped[list["Task"]] = relationship(back_populates="company")

    __table_args__ = (
        # Частичный уникальный индекс на ИНН (только не‑NULL значения)
        Index("idx_companies_inn_unique", "inn", unique=True, postgresql_where=inn.isnot(None)),
    )