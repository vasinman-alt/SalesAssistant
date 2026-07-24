# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.deal.
"""
import uuid
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import ForeignKey, Uuid, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sales_assistant.db.base import Base, UUIDPK
from sales_assistant.db.models.mixins import SyncFieldsMixin

class Deal(Base, SyncFieldsMixin):
    __tablename__ = "deals"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"))
    title: Mapped[str]
    stage: Mapped[str]  # lead, qualified, proposal_sent, negotiation, won, lost
    amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(default="RUB")
    expected_close_date: Mapped[date | None]
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)