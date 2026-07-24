# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.custom_field.
"""
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column
from sales_assistant.db.base import Base, UUIDPK

class CustomFieldDefinition(Base):
    __tablename__ = "custom_field_definitions"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    entity_type: Mapped[str]  # 'company', 'contact'
    field_key: Mapped[str]
    field_label: Mapped[str]
    field_type: Mapped[str]  # text, number, date, select
    select_options: Mapped[dict | None] = mapped_column(JSON)
    sort_order: Mapped[int]