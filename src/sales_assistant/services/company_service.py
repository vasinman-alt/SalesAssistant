# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.services.company_service.

Сервис для работы с предприятиями.
"""
import uuid as _uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sales_assistant.db.models.company import Company
from sales_assistant.db.models.document import DocumentLink
from sales_assistant.repositories.company_repository import CompanyRepository
from sales_assistant.services.interaction_service import InteractionService
from sales_assistant.config.settings import get_node_id

logger = logging.getLogger(__name__)
NODE_ID = get_node_id()


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
        display_name: Optional[str] = None,
        legal_name: Optional[str] = None,
    ) -> Company:
        company = Company(
            id=_uuid.uuid4(),
            name=name,
            display_name=display_name,
            legal_name=legal_name,
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
            origin_node=NODE_ID,
            version=1,
            updated_at=datetime.now(timezone.utc),
        )
        self.repo.create(session, company)

        interaction_svc = InteractionService(self.current_user_id)
        interaction_svc.create(
            session,
            company_id=company.id,
            interaction_type="note",
            event_date=datetime.now(timezone.utc),
            subject="Компания создана",
            description="Карточка компании создана.",
        )

        return company

    def update_display_name(self, session: Session, company_id: UUID, display_name: str) -> Optional[Company]:
        company = self.repo.get(session, company_id)
        if company:
            company.display_name = display_name
            company.updated_at = datetime.now(timezone.utc)
            company.version += 1
            session.flush()
        return company

    def update_legal_name(self, session: Session, company_id: UUID, legal_name: str) -> Optional[Company]:
        company = self.repo.get(session, company_id)
        if company:
            company.legal_name = legal_name
            company.updated_at = datetime.now(timezone.utc)
            company.version += 1
            session.flush()
        return company

    def archive(self, session: Session, company_id: UUID) -> Optional[Company]:
        """Мягкое удаление – перевод в статус 'archived'."""
        company = self.repo.get(session, company_id)
        if company:
            company.status = "archived"
            company.updated_at = datetime.now(timezone.utc)
            company.version += 1
            session.flush()
        return company

    def delete_permanently(self, session: Session, company_id: UUID) -> None:
        """Полное физическое удаление (только для администратора)."""
        company = self.repo.get(session, company_id)
        if not company:
            return
        for contact in company.contacts:
            session.delete(contact)
        for interaction in company.interactions:
            session.delete(interaction)
        for task in company.tasks:
            session.delete(task)
        session.query(DocumentLink).filter(
            DocumentLink.entity_type == 'company',
            DocumentLink.entity_id == company.id
        ).delete()
        session.delete(company)
        session.flush()