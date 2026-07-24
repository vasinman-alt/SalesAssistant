# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.repositories.contact_repository.

Репозиторий для работы с контактами.
"""
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sales_assistant.db.models.contact import Contact
from sales_assistant.repositories.base_repository import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    def __init__(self):
        super().__init__(Contact)

    def get_by_company(self, session: Session, company_id: UUID) -> List[Contact]:
        """Получить все контакты компании (включая связанные телефоны/email/мессенджеры)."""
        return (
            session.query(Contact)
            .filter(Contact.company_id == company_id)
            .options(
                joinedload(Contact.phones),
                joinedload(Contact.emails),
                joinedload(Contact.messengers),
            )
            .order_by(Contact.full_name)
            .all()
        )