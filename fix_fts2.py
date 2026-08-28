import sqlite3

conn = sqlite3.connect("data/sales.db")
cursor = conn.cursor()
# Удаляем записи о виртуальных таблицах из системной таблицы
cursor.execute("DELETE FROM sqlite_master WHERE type='table' AND name LIKE 'fts_%'")
cursor.execute("DELETE FROM sqlite_master WHERE type='table' AND name = 'search_meta'")
# Также удаляем возможные триггеры и индексы, связанные с FTS
cursor.execute("DELETE FROM sqlite_master WHERE type='index' AND name LIKE 'fts_%'")
cursor.execute("DELETE FROM sqlite_master WHERE type='trigger' AND name LIKE 'fts_%'")
conn.commit()
conn.execute("VACUUM")
conn.close()
print("Следы FTS удалены из sqlite_master, выполнен VACUUM.")