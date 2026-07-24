# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.services.company_service.

Сервис для управления предприятиями.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from sales_assistant.db.models.company import Company
from sales_assistant.db.models.interaction import Interaction
from sales_assistant.db.engine import SessionLocal
from sales_assistant.repositories.company_repository import CompanyRepository


class CompanyService:
    """Сервис для работы с предприятиями."""

    def __init__(self, current_user_id: uuid.UUID):
        self.current_user_id = current_user_id
        self.company_repo = CompanyRepository()

    def create(self, session: Session, name: str, **kwargs) -> Company:
        """
        Создать новую компанию и автоматически добавить первую запись в историю.
        """
        # Генерируем origin_node для синхронизации (пока используем текущий user_id)
        now = datetime.now(timezone.utc)
        company = Company(
            id=uuid.uuid4(),
            name=name,
            created_by=self.current_user_id,
            origin_node=self.current_user_id,
            updated_at=now,
            **kwargs,
        )
        company = self.company_repo.create(session, company)

        # Автоматическая запись в историю
        interaction = Interaction(
            id=uuid.uuid4(),
            company_id=company.id,
            type="note",
            event_date=now,
            entry_date=now,
            subject="Создание карточки компании",
            created_by=self.current_user_id,
            origin_node=self.current_user_id,
        )
        session.add(interaction)
        session.flush()

        return company

    def update(self, session: Session, company: Company) -> Company:
        """Обновить данные компании (обновляет updated_at автоматически)."""
        company.updated_at = datetime.now(timezone.utc)
        return self.company_repo.update(session, company)

    def get_active(self, session: Session, skip=0, limit=100) -> List[Company]:
        return self.company_repo.get_active(session, skip, limit)

    def search(self, session: Session, query: str) -> List[Company]:
        return self.company_repo.search(session, query)

    def get_by_id(self, session: Session, company_id: uuid.UUID) -> Optional[Company]:
        return self.company_repo.get(session, company_id)