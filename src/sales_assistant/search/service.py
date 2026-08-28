# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.search.service.

Сервис поиска предприятий (только Checko).
"""
import uuid
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sales_assistant.search.checko_client import CheckoClient
from sales_assistant.services.company_service import CompanyService
from sales_assistant.db.models.company import Company
from sales_assistant.db.models.region import Region
from sales_assistant.db.models.contact import Contact, ContactPhone, ContactEmail
from sales_assistant.config.settings import get_node_id

logger = logging.getLogger(__name__)
NODE_ID = get_node_id()


class SearchService:
    def __init__(self, current_user_id: uuid.UUID, checko_api_key: str = ""):
        self.current_user_id = current_user_id
        self.checko = CheckoClient(checko_api_key) if checko_api_key else None
        self.last_api_meta: Dict[str, Any] = {}

    def search_online(self, query: str, region_code: str = "",
                      okved: str = "", only_active: Optional[bool] = True,
                      max_results: int = 100, by: str = "") -> List[Dict]:
        """
        Поиск организаций. Если by='okved', ищет только по коду ОКВЭД.
        Возвращает базовый список без оборотов.
        """
        if not self.checko:
            raise Exception("API-ключ Checko не задан. Сохраните ключ в настройках.")

        if not query:
            raise Exception("Введите название, ИНН или код ОКВЭД для поиска.")

        # Определяем тип поиска, если не задан явно
        if not by:
            by = "name"
            if query.isdigit():
                if len(query) == 10:
                    by = "inn"
                elif len(query) == 13:
                    by = "ogrn"

        results = []
        page = 1
        while len(results) < max_results:
            resp = self.checko.search(
                query=query,
                by=by,
                obj="org",
                region=region_code if region_code else None,
                okved=okved if by != "okved" else None,   # при by=okved фильтр оквэд не передаём
                active=only_active,
                limit=min(100, max_results - len(results)),
                page=page
            )
            self.last_api_meta = resp.get("meta", {})
            entries = resp.get("data", {}).get("Записи", [])
            if not entries:
                break
            for entry in entries:
                results.append({
                    "ogrn": entry.get("ОГРН", ""),
                    "inn": entry.get("ИНН", ""),
                    "kpp": entry.get("КПП", ""),
                    "name": entry.get("НаимСокр", ""),
                    "full_name": entry.get("НаимПолн", ""),
                    "legal_address": entry.get("ЮрАдрес", ""),
                    "okved_main": entry.get("ОКВЭД", ""),
                    "region_code": entry.get("РегионКод", ""),
                    "status": entry.get("Статус", ""),
                    "revenue": 0,
                })
            page += 1
            total_pages = resp.get("data", {}).get("СтрВсего", 1)
            if page > total_pages:
                break

        return results

    def fetch_finances_for(self, company_data: dict) -> float:
        """Получить выручку за последний отчётный год. Возвращает 0, если данных нет."""
        if not self.checko:
            return 0.0
        try:
            inn = company_data.get("inn")
            ogrn = company_data.get("ogrn")
            fin = self.checko.get_finances(ogrn=ogrn if ogrn else None, inn=inn if inn else None)
            years_data = fin.get("data", {})
            if years_data:
                latest_year = max(years_data.keys(), key=int)
                year_data = years_data[latest_year]
                rev = year_data.get("2110", 0)
                if isinstance(rev, dict):
                    rev = rev.get("СумОтч", 0)
                return rev or 0.0
        except Exception as e:
            logger.warning(f"Не удалось получить выручку для {company_data.get('name')}: {e}")
        return 0.0

    def create_and_enrich_company(self, session: Session, search_result: Dict) -> uuid.UUID:
        """
        Создаёт компанию на основе поисковой выдачи и сразу обогащает её.
        Возвращает ID компании.
        """
        service = CompanyService(self.current_user_id)

        region_id = None
        region_code = search_result.get("region_code")
        if region_code:
            region = session.query(Region).filter(Region.code == region_code).first()
            if not region:
                region = Region(id=uuid.uuid4(), code=region_code, name=region_code)
                session.add(region)
                session.flush()
            region_id = region.id

        company = service.create(
            session,
            name=search_result.get("name", search_result.get("full_name", "")),
            inn=search_result.get("inn"),
            region_id=region_id,
            legal_address=search_result.get("legal_address"),
            actual_address=search_result.get("legal_address"),
            legal_name=search_result.get("full_name"),
            comment=f"Импортировано из поиска. ОГРН: {search_result.get('ogrn')}. ОКВЭД: {search_result.get('okved_main')}",
            source="search"
        )
        session.flush()
        self._enrich_company_sync(session, company)
        session.commit()
        return company.id

    def _enrich_company_sync(self, session: Session, company: Company):
        """
        Синхронное обогащение (выполняется внутри транзакции создания).
        Использует /company и /finances.
        """
        if not self.checko:
            return

        try:
            # 1. Детальная информация
            details = self.checko.get_company(inn=company.inn or None, ogrn=None)
            data = details.get("data", {})
            # Регион и адрес
            region_info = data.get("Регион", {})
            if region_info.get("Код") and not company.region:
                region = session.query(Region).filter(Region.code == region_info["Код"]).first()
                if not region:
                    region = Region(id=uuid.uuid4(), code=region_info["Код"], name=region_info.get("Наим", ""))
                    session.add(region)
                    session.flush()
                company.region_id = region.id
            addr = data.get("ЮрАдрес", {}).get("АдресРФ")
            if addr:
                company.legal_address = addr

            # Руководитель
            mgmt = data.get("Руковод", [])
            if mgmt:
                head = mgmt[0]
                name = head.get("ФИО", "")
                position = head.get("НаимДолжн", "")
                if name:
                    company.comment = (company.comment or "") + f"\nРуководитель: {name} ({position})"

            # Контакты
            contacts = data.get("Контакты", {})
            phones = contacts.get("Тел", [])
            emails = contacts.get("Емэйл", [])
            website = contacts.get("ВебСайт")
            if phones:
                contact = Contact(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    contact_type='phone_shared',
                    full_name='Телефон из ЕГРЮЛ',
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    origin_node=NODE_ID,
                    version=1
                )
                session.add(contact)
                session.flush()
                for p in phones:
                    session.add(ContactPhone(id=uuid.uuid4(), contact_id=contact.id, phone=p))
            if emails:
                contact = Contact(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    contact_type='email_shared',
                    full_name='Email из ЕГРЮЛ',
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    origin_node=NODE_ID,
                    version=1
                )
                session.add(contact)
                session.flush()
                for e in emails:
                    session.add(ContactEmail(id=uuid.uuid4(), contact_id=contact.id, email=e))
            if website and not company.website:
                company.website = website

            # 2. Выручка
            fin = self.checko.get_finances(inn=company.inn, ogrn=None)
            years = fin.get("data", {})
            if years:
                latest = max(years.keys(), key=int)
                year_data = years[latest]
                rev = year_data.get("2110", 0)
                if isinstance(rev, dict):
                    rev = rev.get("СумОтч", 0)
                if rev:
                    if not company.custom_fields:
                        company.custom_fields = {}
                    company.custom_fields["revenue"] = rev
                    company.comment = (company.comment or "") + f"\nВыручка за {latest}: {rev:,} руб."

        except Exception as e:
            logger.error(f"Ошибка обогащения компании {company.name}: {e}")