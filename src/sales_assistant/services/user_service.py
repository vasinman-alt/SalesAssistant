# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.services.user_service.

Сервис управления пользователями. При первом запуске создаёт
локального пользователя с ролью owner.
"""
import uuid
from sqlalchemy.orm import Session
from sales_assistant.db.engine import SessionLocal
from sales_assistant.db.models.user import User, Role, UserRole


class UserService:
    @staticmethod
    def ensure_local_admin() -> uuid.UUID:
        """
        Убеждается, что в базе существует локальный пользователь-владелец.
        Возвращает UUID пользователя.
        """
        session = SessionLocal()
        try:
            # Проверяем, существует ли уже локальный пользователь
            user = session.query(User).filter(User.is_local == True).first()
            if user:
                return user.id

            # Создаём роль owner, если её нет
            owner_role = session.query(Role).filter(Role.name == "owner").first()
            if not owner_role:
                owner_role = Role(id=uuid.uuid4(), name="owner")
                session.add(owner_role)
                session.flush()

            # Создаём пользователя
            local_user = User(
                id=uuid.uuid4(),
                username="local_admin",
                display_name="Администратор",
                is_local=True,
            )
            session.add(local_user)
            session.flush()

            # Связываем с ролью
            user_role = UserRole(user_id=local_user.id, role_id=owner_role.id)
            session.add(user_role)

            session.commit()
            return local_user.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()