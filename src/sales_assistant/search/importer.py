# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.search.importer.

Импорт данных из CSV-выгрузок.
"""
import csv
import os
from typing import List, Dict, Any
import uuid
from sqlalchemy import text
from sales_assistant.db.engine import engine
from sales_assistant.db.models.region import Region


def import_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """Читает CSV-файл предприятий."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        sample = f.read(2048)
        f.seek(0)
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample, delimiters=';,')
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(f, dialect=dialect)
        records = []
        for row in reader:
            record = {
                'ogrn': row.get('ogrn', '').strip(),
                'inn': row.get('inn', '').strip(),
                'name': row.get('name', '').strip(),
                'full_name': row.get('full_name', '').strip(),
                'legal_address': row.get('legal_address', '').strip(),
                'okved_main': row.get('okved_main', '').strip(),
                'okved_list': row.get('okved_list', '').strip(),
                'region_code': row.get('region_code', '').strip(),
                'status': row.get('status', '').strip(),
                'revenue': row.get('revenue', '').strip() or '0',
            }
            if record['name'] or record['full_name']:
                records.append(record)
        return records


def import_regions_from_csv(file_path: str):
    """Загружает справочник регионов (code, name) в таблицу regions.
    Файл CSV с колонками: code, name. Разделитель ; или ,.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        sample = f.read(2048)
        f.seek(0)
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample, delimiters=';,')
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(f, dialect=dialect)
        with engine.begin() as conn:
            for row in reader:
                code = row.get('code', '').strip()
                name = row.get('name', '').strip()
                if not code or not name:
                    continue
                # Проверим, нет ли уже такого кода
                existing = conn.execute(
                    text("SELECT id FROM regions WHERE code = :code"),
                    {"code": code}
                ).scalar()
                if not existing:
                    region = Region(id=uuid.uuid4(), name=name, code=code)
                    conn.execute(
                        text("INSERT INTO regions (id, name, code) VALUES (:id, :name, :code)"),
                        {"id": str(region.id), "name": name, "code": code}
                    )