# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.services.company_service.

Сервис для работы с предприятиями.
"""
import uuid as _uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sales_assistant.db.models.company import Company
from sales_assistant.repositories.company_repository import CompanyRepository
from sales_assistant.services.interaction_service import InteractionService


class CompanyService:
    def __init__(self, current_user_id: UUID):
        self.current_user_id = current_user_id
        self.repo = CompanyRepository()

    def get_active(self, session: Session) -> List[Company]:
        return self.repo.get_active(session)

    def search(self, session: Session, query: str) -> List[Company]:
        return self.repo.search(session, query)

    def get_by_id(self, session: Session, company_id: UUID) -> Optional[Company]:
        return self.repo.get(session, company_id)

    def create(
        self,
        session: Session,
        name: str,
        inn: Optional[str] = None,
        region_id: Optional[UUID] = None,
        legal_address: Optional[str] = None,
        actual_address: Optional[str] = None,
        website: Optional[str] = None,
        comment: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Company:
        company = Company(
            id=_uuid.uuid4(),
            name=name,
            inn=inn,
            region_id=region_id,
            legal_address=legal_address,
            actual_address=actual_address,
            website=website,
            comment=comment,
            source=source,
            status="active",
            created_at=datetime.now(timezone.utc),
            created_by=self.current_user_id,
            origin_node=_uuid.uuid4(),
            version=1,
            updated_at=datetime.now(timezone.utc),
        )
        self.repo.create(session, company)

        # Автоматически добавляем первую запись в историю
        interaction_svc = InteractionService(self.current_user_id)
        interaction_svc.create(
            session,
            company_id=company.id,
            interaction_type="note",
            event_date=datetime.now(timezone.utc),
            subject="Компания создана",
            description="Карточка компании создана вручную.",
        )

        return company