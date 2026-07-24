# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.user.
"""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Uuid, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sales_assistant.db.base import Base, UUIDPK

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    display_name: Mapped[str | None]
    is_local: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Связи
    roles: Mapped[list["Role"]] = relationship(secondary="user_roles", back_populates="users")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(secondary="user_roles", back_populates="roles")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("roles.id"), primary_key=True)