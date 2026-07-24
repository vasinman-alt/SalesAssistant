# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.services.contact_service.

Сервис для управления контактами.
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sales_assistant.db.models.contact import Contact
from sales_assistant.repositories.contact_repository import ContactRepository


class ContactService:
    """Сервис для работы с контактами."""

    def __init__(self, current_user_id: uuid.UUID):
        self.current_user_id = current_user_id
        self.contact_repo = ContactRepository()

    def get_by_company(self, session: Session, company_id: uuid.UUID) -> List[Contact]:
        return self.contact_repo.get_by_company(session, company_id)

    def get_by_id(self, session: Session, contact_id: uuid.UUID) -> Optional[Contact]:
        return self.contact_repo.get(session, contact_id)

    def create(self, session: Session, company_id: uuid.UUID, contact_type: str, full_name: str,
               **kwargs) -> Contact:
        contact = Contact(
            id=uuid.uuid4(),
            company_id=company_id,
            contact_type=contact_type,
            full_name=full_name,
            origin_node=self.current_user_id,  # временно user_id
            **kwargs,
        )
        return self.contact_repo.create(session, contact)

    def update(self, session: Session, contact: Contact) -> Contact:
        return self.contact_repo.update(session, contact)