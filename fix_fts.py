import sqlite3

conn = sqlite3.connect("data/sales.db")
cursor = conn.cursor()
# Удаляем все FTS-таблицы и search_meta
for table in ["fts_enterprises", "fts_enterprises_data", "fts_enterprises_idx",
              "fts_enterprises_content", "fts_enterprises_docsize", "fts_enterprises_config",
              "search_meta"]:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    except:
        pass
conn.commit()
conn.close()
print("Виртуальные таблицы удалены.")