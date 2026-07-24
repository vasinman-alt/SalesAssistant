# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.models.document.
"""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sales_assistant.db.base import Base, UUIDPK

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUIDPK] = mapped_column(primary_key=True)
    file_path: Mapped[str]  # data/documents/<company_id>/<filename>
    original_name: Mapped[str]
    doc_type: Mapped[str]  # offer, contract, invoice, spec, photo, presentation, other
    status: Mapped[str] = mapped_column(default="active")
    uploaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    origin_node: Mapped[uuid.UUID]

    links: Mapped[list["DocumentLink"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentLink(Base):
    __tablename__ = "document_links"

    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("documents.id"), primary_key=True)
    entity_type: Mapped[str] = mapped_column(primary_key=True)  # 'company', 'contact', 'interaction', 'task'
    entity_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    document: Mapped["Document"] = relationship(back_populates="links")