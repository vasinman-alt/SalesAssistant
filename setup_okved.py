# -*- coding: utf-8 -*-
"""
Загрузка справочника ОКВЭД из SQL-файла (PostgreSQL дамп).
Поместите файл okved.sql в папку data/imports/.
"""
import sqlite3
import os
import re

DB_PATH = "data/sales.db"
SQL_FILE = "data/imports/okved.sql"

if not os.path.exists(SQL_FILE):
    print(f"Файл {SQL_FILE} не найден. Поместите SQL-дамп в эту папку.")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Создаём таблицу, если её нет
cursor.execute("""
CREATE TABLE IF NOT EXISTS okved (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
""")

try:
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Убираем все упоминания "public." перед именами таблиц
    sql_content = re.sub(r'\bpublic\.', '', sql_content)

    # Извлекаем отдельные INSERT-запросы (могут быть многострочные)
    # Простой способ: выполняем весь скрипт, но игнорируем ошибки на CREATE
    # Для надёжности разобьём по точкам с запятой и выполним только INSERT
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    for stmt in statements:
        if stmt.upper().startswith('INSERT'):
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"Пропущена ошибочная строка: {e}")

    conn.commit()
    print("Справочник ОКВЭД успешно загружен из SQL-файла.")
except Exception as e:
    print(f"Ошибка при загрузке: {e}")
    conn.rollback()
finally:
    conn.close()