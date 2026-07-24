# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.repositories.interaction_repository.

Репозиторий для работы с взаимодействиями.
"""
from sales_assistant.db.models.interaction import Interaction
from sales_assistant.repositories.base_repository import BaseRepository


class InteractionRepository(BaseRepository[Interaction]):
    def __init__(self):
        super().__init__(Interaction)