# -*- coding: utf-8 -*-
"""
Пакет tests.test_models.
"""
import uuid
from sales_assistant.db.models import Company, Region

def test_create_company(db_session):
    region = Region(id=uuid.uuid4(), name="Moscow", code="MSK")
    db_session.add(region)
    db_session.flush()

    company = Company(
        id=uuid.uuid4(),
        name="Test Corp",
        region_id=region.id,
        status="active",
        origin_node=uuid.uuid4(),
    )
    db_session.add(company)
    db_session.commit()

    assert company.id is not None
    assert company.region.name == "Moscow"