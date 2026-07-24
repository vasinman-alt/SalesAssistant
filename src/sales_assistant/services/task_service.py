# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.services.task_service.

Сервис для управления задачами.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sales_assistant.db.models.task import Task
from sales_assistant.repositories.task_repository import TaskRepository


class TaskService:
    def __init__(self, current_user_id: uuid.UUID):
        self.current_user_id = current_user_id
        self.repo = TaskRepository()

    def get_by_company(self, session: Session, company_id: uuid.UUID) -> List[Task]:
        """Получить все задачи компании."""
        return (
            session.query(Task)
            .filter(Task.company_id == company_id)
            .order_by(Task.due_date.asc())
            .all()
        )

    def create(
        self,
        session: Session,
        company_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        priority: str = "medium",
        contact_id: Optional[uuid.UUID] = None,
        interaction_id: Optional[uuid.UUID] = None,
    ) -> Task:
        """Создать новую задачу."""
        task = Task(
            id=uuid.uuid4(),
            company_id=company_id,
            contact_id=contact_id,
            interaction_id=interaction_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status="open",
            assignee_id=self.current_user_id,  # Пока назначаем на себя
            created_at=datetime.now(timezone.utc),
            origin_node=uuid.uuid4(),
            version=1,
            updated_at=datetime.now(timezone.utc),
        )
        self.repo.create(session, task)
        return task

    def update_status(self, session: Session, task_id: uuid.UUID, status: str) -> Task:
        task = self.repo.get(session, task_id)
        if task:
            task.status = status
            if status == "done":
                task.completed_at = datetime.now(timezone.utc)
            # Примечание: в сервисе мы не вызываем flush/commit, это делает вызывающий код
        return task