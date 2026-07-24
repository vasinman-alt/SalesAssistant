# -*- coding: utf-8 -*-
"""
Пакет tests.test_migrations.
"""
from sales_assistant.db.base import Base

def test_all_tables_present():
    required_tables = {
        "regions", "activities", "companies", "company_activities",
        "contacts", "contact_phones", "contact_emails", "contact_messengers",
        "interactions", "tasks", "documents", "document_links",
        "tags", "entity_tags", "custom_field_definitions",
        "users", "roles", "user_roles", "deals", "sync_conflict_log",
    }
    existing = set(Base.metadata.tables.keys())
    missing = required_tables - existing
    assert not missing, f"Missing tables: {missing}"