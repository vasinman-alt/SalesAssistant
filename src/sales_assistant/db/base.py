# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.base.

Декларативная база моделей SQLAlchemy.
"""
import uuid
from sqlalchemy import Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing_extensions import Annotated

UUIDPK = Annotated[uuid.UUID, mapped_column(Uuid, primary_key=True, default=uuid.uuid4)]

class Base(DeclarativeBase):
    pass