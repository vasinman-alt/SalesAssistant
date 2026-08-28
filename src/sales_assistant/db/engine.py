# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.db.engine.

Создание движка SQLAlchemy и фабрики сессий для SQLite.
"""
import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from sales_assistant.config.paths import DB_FILE

engine = create_engine(
    f"sqlite:///{DB_FILE}",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)

@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    """Включаем foreign_keys и регистрируем unicode LOWER/UPPER для кириллицы."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()

    # Подменяем встроенные SQLite-функции на Python-реализации, которые корректно работают с юникодом
    dbapi_connection.create_function("LOWER", 1, lambda s: s.lower() if s is not None else None)
    dbapi_connection.create_function("UPPER", 1, lambda s: s.upper() if s is not None else None)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)