# -*- coding: utf-8 -*-
"""
Репозиторий для работы с предприятиями.
Регистронезависимый поиск (латиница + кириллица) через Python-функцию LOWER.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from sales_assistant.db.models.company import Company
from sales_assistant.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self):
        super().__init__(Company)

    def get_active(self, session: Session, skip: int = 0, limit: int = 100) -> List[Company]:
        return (
            session.query(Company)
            .filter(Company.status == "active")
            .order_by(func.lower(Company.name))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(self, session: Session, query: str, max_results: int = 50) -> List[Company]:
        """Регистронезависимый поиск по названию (display_name/name) и ИНН."""
        pattern = f"%{query.lower()}%"
        return (
            session.query(Company)
            .filter(
                or_(
                    func.lower(Company.name).like(pattern),
                    func.lower(Company.display_name).like(pattern),
                    Company.inn.like(f"%{query}%"),  # ИНН – цифры, регистр неважен
                )
            )
            .order_by(func.lower(Company.name))
            .limit(max_results)
            .all()
        )