# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.migrations.env.

Конфигурация Alembic для работы с моделями SalesAssistant.
"""
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from sales_assistant.db.base import Base
from sales_assistant.db.models import *  # noqa: F401, F403
from sales_assistant.config.paths import DB_FILE

config = context.config

if config.config_file_name is not None:
    import logging
    logging.basicConfig(level=logging.INFO)

target_metadata = Base.metadata

# Исключаем виртуальные FTS-таблицы и служебную search_meta
def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table" and (name.startswith("fts_") or name == "search_meta"):
        return False
    return True

def run_migrations_offline():
    url = f"sqlite:///{DB_FILE}"
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    from sales_assistant.db.engine import engine
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()