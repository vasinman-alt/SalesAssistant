# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.ui.themes.theme_manager.

Загрузка и применение QSS-тем.
"""
from pathlib import Path
from PySide6.QtWidgets import QApplication

THEMES_DIR = Path(__file__).parent
AVAILABLE_THEMES = ["classic", "modern", "dark", "compact"]

def apply_theme(app: QApplication, theme_name: str) -> None:
    """Применяет QSS-таблицу стилей для указанной темы."""
    qss_file = THEMES_DIR / f"{theme_name}.qss"
    if qss_file.exists():
        with open(qss_file, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        app.setStyleSheet("")