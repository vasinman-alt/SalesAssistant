# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.contact.
"""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sales_assistant.db.base import Base, UUIDPK
from sales_assistant.db.models.mixins import SyncFieldsMixin

class Contact(Base, SyncFieldsMixin):
    __tablename__ = "contacts"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("companies.id"))
    contact_type: Mapped[str] = mapped_column(nullable=False)  # person, phone_shared, email_shared, telegram, whatsapp, department, reception
    full_name: Mapped[str | None]
    position: Mapped[str | None]
    department: Mapped[str | None]
    comment: Mapped[str | None]
    custom_fields: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(default="active")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Связи
    company: Mapped["Company"] = relationship(back_populates="contacts")
    phones: Mapped[list["ContactPhone"]] = relationship(back_populates="contact", cascade="all, delete-orphan")
    emails: Mapped[list["ContactEmail"]] = relationship(back_populates="contact", cascade="all, delete-orphan")
    messengers: Mapped[list["ContactMessenger"]] = relationship(back_populates="contact", cascade="all, delete-orphan")


class ContactPhone(Base):
    __tablename__ = "contact_phones"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id"))
    phone: Mapped[str] = mapped_column(nullable=False)
    label: Mapped[str | None]

    contact: Mapped["Contact"] = relationship(back_populates="phones")


class ContactEmail(Base):
    __tablename__ = "contact_emails"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id"))
    email: Mapped[str] = mapped_column(nullable=False)
    label: Mapped[str | None]

    contact: Mapped["Contact"] = relationship(back_populates="emails")


class ContactMessenger(Base):
    __tablename__ = "contact_messengers"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id"))
    type: Mapped[str]  # telegram, whatsapp, etc.
    value: Mapped[str]

    contact: Mapped["Contact"] = relationship(back_populates="messengers")