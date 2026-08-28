# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.search.schema.

Схема FTS5 индекса и вспомогательной таблицы для хранения метаданных поиска.
"""
CREATE_FTS_TABLE = """
CREATE VIRTUAL TABLE IF NOT EXISTS fts_enterprises USING fts5(
    ogrn,
    inn,
    name,
    full_name,
    legal_address,
    okved_main,
    okved_list,
    region_code,
    status,
    revenue,
    tokenize='unicode61'
);
"""

CREATE_META_TABLE = """
CREATE TABLE IF NOT EXISTS search_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

INSERT_FTS = """
INSERT INTO fts_enterprises (ogrn, inn, name, full_name, legal_address, okved_main, okved_list, region_code, status, revenue)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# Поиск с текстовым запросом (непустой)
SEARCH_QUERY_WITH_MATCH = """
SELECT ogrn, inn, name, full_name, legal_address, okved_main, okved_list, region_code, status, revenue
FROM fts_enterprises
WHERE fts_enterprises MATCH ?
  AND (? = '' OR region_code = ?)
  AND (? = '' OR okved_main LIKE ?)
  AND (? = '' OR CAST(revenue AS REAL) >= CAST(? AS REAL))
  AND (? = 0 OR status = 'действующее')
ORDER BY rank
LIMIT ?
"""

# Поиск без текстового запроса (все записи, только фильтры)
SEARCH_QUERY_NO_MATCH = """
SELECT ogrn, inn, name, full_name, legal_address, okved_main, okved_list, region_code, status, revenue
FROM fts_enterprises
WHERE (? = '' OR region_code = ?)
  AND (? = '' OR okved_main LIKE ?)
  AND (? = '' OR CAST(revenue AS REAL) >= CAST(? AS REAL))
  AND (? = 0 OR status = 'действующее')
ORDER BY name
LIMIT ?
"""