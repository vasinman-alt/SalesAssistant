# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.config.paths.

Определяет пути к данным приложения в зависимости от режима установки
(portable или installed) и обеспечивает создание структуры директорий.
"""

import os
import sys
from pathlib import Path


def _get_app_dir() -> Path:
    """Возвращает корневую папку приложения."""
    if getattr(sys, 'frozen', False):
        # PyInstaller: папка с exe
        return Path(sys.executable).parent
    else:
        # Разработка: текущая рабочая директория (должна быть корнем проекта)
        return Path.cwd()


def _get_data_dir() -> Path:
    r"""
    Определяет базовую папку для данных.
    Если в папке с приложением есть data/ и она доступна для записи — portable.
    Иначе — %LOCALAPPDATA%\SalesAssistant\data (installed).
    """
    app_dir = _get_app_dir()
    portable_data = app_dir / "data"
    if portable_data.is_dir():
        if os.access(portable_data, os.W_OK):
            return portable_data

    local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return local_appdata / "SalesAssistant" / "data"


# --- Инициализация при импорте ---
APP_DIR = _get_app_dir()
_DATA_DIR = _get_data_dir()

DB_FILE = _DATA_DIR / "sales.db"
BACKUPS_DIR = _DATA_DIR / "backups"
CACHE_DIR = _DATA_DIR / "cache"
IMPORTS_DIR = _DATA_DIR / "imports"
DOCUMENTS_DIR = _DATA_DIR / "documents"

APP_SETTINGS_FILE = CACHE_DIR / "app_settings.json"
UI_STATE_FILE = CACHE_DIR / "ui_state.json"

ALEMBIC_INI_FILE = APP_DIR / "alembic.ini"


def ensure_data_dirs() -> None:
    """Создаёт все необходимые директории для данных, если их нет."""
    dirs = [BACKUPS_DIR, CACHE_DIR, IMPORTS_DIR, DOCUMENTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def is_portable() -> bool:
    """Возвращает True, если приложение работает в portable-режиме."""
    return _DATA_DIR == APP_DIR / "data"