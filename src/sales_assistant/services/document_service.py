# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.services.document_service.

Сервис для работы с документами.
"""
import uuid
import os
import shutil
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sales_assistant.db.models.document import Document, DocumentLink
from sales_assistant.repositories.document_repository import DocumentRepository
from sales_assistant.config.paths import DOCUMENTS_DIR
from sales_assistant.config.settings import get_node_id

logger = logging.getLogger(__name__)
NODE_ID = get_node_id()

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
        source_path: str,
        original_name: str,
        doc_type: str,
        entity_type: str,
        entity_id: uuid.UUID,
        comment: Optional[str] = None,
    ) -> Document:
        """
        Копирует файл из source_path в DOCUMENTS_DIR/<entity_id>/<original_name>
        и создаёт запись в базе.
        """
        # Создаём папку назначения
        dest_dir = DOCUMENTS_DIR / str(entity_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Генерируем уникальное имя файла, если такой уже существует
        dest_name = original_name
        counter = 1
        base, ext = os.path.splitext(original_name)
        while (dest_dir / dest_name).exists():
            dest_name = f"{base}_{counter}{ext}"
            counter += 1
        dest_path = dest_dir / dest_name

        # Копируем файл с метаданными
        try:
            shutil.copy2(source_path, dest_path)
        except Exception as e:
            logger.error(f"Ошибка копирования файла {source_path} -> {dest_path}: {e}")
            raise

        doc = Document(
            id=uuid.uuid4(),
            file_path=str(dest_path),
            original_name=dest_name,
            doc_type=doc_type,
            comment=comment,
            uploaded_at=datetime.now(timezone.utc),
            uploaded_by=self.current_user_id,
            origin_node=NODE_ID,
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
        """Удаляет запись и, опционально, сам файл."""
        doc = session.get(Document, document_id)
        if not doc:
            return False
        if delete_file and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception as e:
                logger.error(f"Ошибка удаления файла {doc.file_path}: {e}")
        session.query(DocumentLink).filter(DocumentLink.document_id == document_id).delete()
        session.delete(doc)
        session.flush()
        return True

    def update_comment(self, session: Session, document_id: uuid.UUID, comment: str) -> Optional[Document]:
        doc = session.get(Document, document_id)
        if doc:
            doc.comment = comment
            session.flush()
        return doc