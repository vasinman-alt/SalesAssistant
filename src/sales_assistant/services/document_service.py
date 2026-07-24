# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.services.document_service.

Сервис для работы с документами.
"""
import uuid
import os
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sales_assistant.db.models.document import Document, DocumentLink
from sales_assistant.repositories.document_repository import DocumentRepository


class DocumentService:
    def __init__(self, current_user_id: uuid.UUID):
        self.current_user_id = current_user_id
        self.repo = DocumentRepository()

    def get_by_entity(self, session: Session, entity_type: str, entity_id: uuid.UUID) -> List[Document]:
        return (
            session.query(Document)
            .join(DocumentLink)
            .filter(
                DocumentLink.entity_type == entity_type,
                DocumentLink.entity_id == entity_id,
            )
            .all()
        )

    def attach_to_entity(
        self,
        session: Session,
        file_path: str,
        original_name: str,
        doc_type: str,
        entity_type: str,
        entity_id: uuid.UUID,
        comment: Optional[str] = None,
    ) -> Document:
        doc = Document(
            id=uuid.uuid4(),
            file_path=file_path,
            original_name=original_name,
            doc_type=doc_type,
            comment=comment,
            uploaded_at=datetime.now(timezone.utc),
            uploaded_by=self.current_user_id,
            origin_node=uuid.uuid4(),
        )
        session.add(doc)
        session.flush()

        link = DocumentLink(
            document_id=doc.id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        session.add(link)
        return doc

    def remove(self, session: Session, document_id: uuid.UUID, delete_file: bool = False) -> bool:
        doc = session.get(Document, document_id)
        if not doc:
            return False
        session.query(DocumentLink).filter(DocumentLink.document_id == document_id).delete()
        session.delete(doc)
        if delete_file:
            try:
                if os.path.exists(doc.file_path):
                    os.remove(doc.file_path)
            except Exception:
                pass
        session.flush()
        return True

    def update_comment(self, session: Session, document_id: uuid.UUID, comment: str) -> Optional[Document]:
        doc = session.get(Document, document_id)
        if doc:
            doc.comment = comment
            session.flush()
        return doc