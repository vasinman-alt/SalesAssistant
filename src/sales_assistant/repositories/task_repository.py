# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.repositories.task_repository.

Репозиторий для работы с задачами.
"""
from sales_assistant.db.models.task import Task
from sales_assistant.repositories.base_repository import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self):
        super().__init__(Task)