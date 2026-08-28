import sqlite3

conn = sqlite3.connect("data/sales.db")
conn.execute("UPDATE alembic_version SET version_num = 'b321a4fae991'")
conn.commit()
conn.close()
print("Ревизия обновлена.")