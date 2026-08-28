# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.config.settings.

Управление настройками приложения, хранящимися в data/cache/app_settings.json.
"""
import json
import uuid
from pathlib import Path
from typing import Any, Dict

from .paths import APP_SETTINGS_FILE, CACHE_DIR

DEFAULTS: Dict[str, Any] = {
    "theme": "classic",
    "language": "ru",
    "modules": {
        "deals": False,
    },
    "first_run": True,
    "checko_api_key": "",
    "node_id": str(uuid.uuid4()),   # ← единый идентификатор узла
}

_cache: Dict[str, Any] | None = None

def _load() -> Dict[str, Any]:
    if not APP_SETTINGS_FILE.exists():
        return DEFAULTS.copy()
    try:
        with open(APP_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULTS.copy()
    merged = DEFAULTS.copy()
    merged.update(data)
    return merged

def _save(data: Dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(APP_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_setting(key: str, default: Any = None) -> Any:
    global _cache
    if _cache is None:
        _cache = _load()
    keys = key.split(".")
    value = _cache
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
        if value is None:
            return default
    return value

def set_setting(key: str, value: Any) -> None:
    global _cache
    if _cache is None:
        _cache = _load()
    keys = key.split(".")
    d = _cache
    for k in keys[:-1]:
        if k not in d or not isinstance(d[k], dict):
            d[k] = {}
        d = d[k]
    d[keys[-1]] = value
    _save(_cache)

def reset_settings() -> None:
    global _cache
    _cache = DEFAULTS.copy()
    _save(_cache)

def get_node_id() -> uuid.UUID:
    """Возвращает сохранённый идентификатор узла."""
    node_str = get_setting("node_id")
    if not node_str:
        node_str = str(uuid.uuid4())
        set_setting("node_id", node_str)
    return uuid.UUID(node_str)