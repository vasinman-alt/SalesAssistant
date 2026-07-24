# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.repositories.document_repository.

Репозиторий для работы с документами.
"""
from sales_assistant.db.models.document import Document
from sales_assistant.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self):
        super().__init__(Document)