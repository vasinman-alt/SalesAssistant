# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.search.indexer.

Построение и обновление полнотекстового индекса предприятий.
"""
from typing import List, Dict, Any
from sqlalchemy import text
from sales_assistant.db.engine import engine
from sales_assistant.search.schema import (
    CREATE_FTS_TABLE, CREATE_META_TABLE, INSERT_FTS
)
from datetime import datetime, timezone


class SearchIndexer:
    def __init__(self):
        self.engine = engine

    def initialize(self):
        """Создаёт таблицы, если их нет."""
        with self.engine.connect() as conn:
            conn.exec_driver_sql(CREATE_FTS_TABLE)
            conn.exec_driver_sql(CREATE_META_TABLE)
            conn.commit()

    def rebuild_index(self, records: List[Dict[str, Any]]):
        """Полностью перестраивает индекс из переданного списка записей."""
        with self.engine.connect() as conn:
            conn.exec_driver_sql("DELETE FROM fts_enterprises")
            for r in records:
                conn.exec_driver_sql(INSERT_FTS, parameters=(
                    r['ogrn'], r['inn'], r['name'], r['full_name'],
                    r['legal_address'], r['okved_main'], r['okved_list'],
                    r['region_code'], r['status'], r.get('revenue')
                ))
            now = datetime.now(timezone.utc).isoformat()
            conn.exec_driver_sql(
                "INSERT OR REPLACE INTO search_meta (key, value) VALUES ('last_updated', ?)",
                parameters=(now,)
            )
            conn.commit()

    def get_last_update(self) -> str:
        """Возвращает строку с датой последнего обновления или None."""
        with self.engine.connect() as conn:
            result = conn.exec_driver_sql(
                "SELECT value FROM search_meta WHERE key = 'last_updated'"
            ).scalar()
            return result