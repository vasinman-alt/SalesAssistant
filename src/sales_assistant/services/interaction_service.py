# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.services.interaction_service.

Сервис для работы с историей взаимодействий (append-only).
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sales_assistant.db.models.interaction import Interaction
from sales_assistant.repositories.interaction_repository import InteractionRepository


class InteractionService:
    def __init__(self, current_user_id: uuid.UUID):
        self.current_user_id = current_user_id
        self.repo = InteractionRepository()

    def get_by_company(self, session: Session, company_id: uuid.UUID) -> List[Interaction]:
        """Получить все взаимодействия по компании (сортировка по дате события по убыванию)."""
        return (
            session.query(Interaction)
            .filter(Interaction.company_id == company_id)
            .order_by(Interaction.event_date.desc())
            .all()
        )

    def create(
        self,
        session: Session,
        company_id: uuid.UUID,
        interaction_type: str,
        event_date: datetime,
        subject: str,
        description: Optional[str] = None,
        contact_id: Optional[uuid.UUID] = None,
        result: Optional[str] = None,
        next_action: Optional[str] = None,
    ) -> Interaction:
        """Создать новое взаимодействие (appends to log)."""
        interaction = Interaction(
            id=uuid.uuid4(),
            company_id=company_id,
            contact_id=contact_id,
            type=interaction_type,
            event_date=event_date,
            entry_date=datetime.now(timezone.utc),
            subject=subject,
            description=description,
            result=result,
            next_action=next_action,
            is_voided=False,
            created_by=self.current_user_id,
            origin_node=uuid.uuid4(),  # Пока генерируем случайный, позже заменится на ID узла
        )
        self.repo.create(session, interaction)
        return interaction