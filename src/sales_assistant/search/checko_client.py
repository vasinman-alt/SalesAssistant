# -*- coding: utf-8 -*-
"""
Клиент для API Checko (поиск, финансы, карточка компании).
"""
import requests
from typing import Dict, Any, Optional

class CheckoClient:
    BASE_URL = "https://api.checko.ru/v2"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.last_meta: Dict[str, Any] = {}

    def _get_meta(self, data: dict) -> dict:
        meta = data.get("meta", {})
        self.last_meta = meta
        if meta.get("status") == "error":
            msg = meta.get("message", "Неизвестная ошибка API Checko")
            raise Exception(msg)
        return meta

    def search(self, query: str, by: str = "name", obj: str = "org",
               region: Optional[str] = None, okved: Optional[str] = None,
               active: Optional[bool] = None, limit: int = 100, page: int = 1) -> Dict[str, Any]:
        """
        Поиск организаций/ИП.
        :param query: текст запроса (мин. 4 символа для by=name)
        :param by: тип поиска ('name', 'okved', 'inn', 'ogrn')
        :param obj: 'org' или 'ent'
        :param region: код региона (2 цифры)
        :param okved: код ОКВЭД (фильтр по основному, если by != 'okved')
        :param active: True - только действующие, False - все, None - без фильтра
        :param limit: до 100
        :param page: страница
        """
        params = {
            "key": self.api_key, "by": by, "obj": obj,
            "query": query, "limit": limit, "page": page,
        }
        if region: params["region"] = region
        if okved and by != "okved": params["okved"] = okved
        if active is not None:
            params["active"] = "true" if active else "false"
        if by == "okved" and okved is None:
            params["codes"] = "all"  # поиск по всем ОКВЭД, если не указан конкретный

        resp = requests.get(f"{self.BASE_URL}/search", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        self._get_meta(data)
        return data

    def get_finances(self, ogrn: Optional[str] = None, inn: Optional[str] = None) -> Dict[str, Any]:
        """Финансовая отчётность."""
        params = {"key": self.api_key}
        if ogrn: params["ogrn"] = ogrn
        elif inn: params["inn"] = inn
        else: raise ValueError("Укажите ОГРН или ИНН")

        resp = requests.get(f"{self.BASE_URL}/finances", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        self._get_meta(data)
        return data

    def get_company(self, ogrn: Optional[str] = None, inn: Optional[str] = None) -> Dict[str, Any]:
        """Детальная информация об организации."""
        params = {"key": self.api_key}
        if ogrn: params["ogrn"] = ogrn
        elif inn: params["inn"] = inn
        else: raise ValueError("Укажите ОГРН или ИНН")

        resp = requests.get(f"{self.BASE_URL}/company", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        self._get_meta(data)
        return data