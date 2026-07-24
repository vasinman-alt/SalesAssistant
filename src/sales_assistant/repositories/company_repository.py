# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.repositories.company_repository.

Репозиторий для работы с предприятиями.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sales_assistant.db.models.company import Company
from sales_assistant.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self):
        super().__init__(Company)

    def get_active(self, session: Session, skip: int = 0, limit: int = 100) -> List[Company]:
        """Получить список активных компаний."""
        return (
            session.query(Company)
            .filter(Company.status == "active")
            .order_by(Company.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(self, session: Session, query: str, max_results: int = 50) -> List[Company]:
        """Поиск компаний по части имени или ИНН."""
        pattern = f"%{query}%"
        return (
            session.query(Company)
            .filter(
                or_(
                    Company.name.ilike(pattern),
                    Company.inn.ilike(pattern),
                )
            )
            .order_by(Company.name)
            .limit(max_results)
            .all()
        )