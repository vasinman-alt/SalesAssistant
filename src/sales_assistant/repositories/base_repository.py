# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.repositories.base_repository.

Базовый репозиторий с типовыми CRUD-операциями.
"""
from typing import TypeVar, Generic, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sales_assistant.db.base import Base

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    """Обобщённый репозиторий для работы с сущностями через SQLAlchemy."""

    def __init__(self, model: type[T]):
        self.model = model

    def get(self, session: Session, id: UUID) -> Optional[T]:
        """Получить объект по первичному ключу."""
        return session.get(self.model, id)

    def get_all(self, session: Session, skip: int = 0, limit: int = 100) -> List[T]:
        """Получить список объектов с пагинацией."""
        return session.query(self.model).offset(skip).limit(limit).all()

    def create(self, session: Session, obj: T) -> T:
        """Добавить новый объект и сразу применить (flush)."""
        session.add(obj)
        session.flush()
        return obj

    def update(self, session: Session, obj: T) -> T:
        """Обновить существующий объект (merge)."""
        session.merge(obj)
        session.flush()
        return obj

    def delete(self, session: Session, id: UUID) -> None:
        """Удалить объект по идентификатору."""
        obj = self.get(session, id)
        if obj:
            session.delete(obj)
            session.flush()