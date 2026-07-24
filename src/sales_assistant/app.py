# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.app.

Точка входа в приложение.
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from sales_assistant.config.settings import get_setting
from sales_assistant.config.paths import ensure_data_dirs, ALEMBIC_INI_FILE
from sales_assistant.ui.main_window import MainWindow
from sales_assistant.ui.themes.theme_manager import apply_theme
from alembic.config import Config
from alembic import command

def main():
    # Создаём структуру данных
    ensure_data_dirs()

    # Применяем миграции
    if ALEMBIC_INI_FILE.exists():
        alembic_cfg = Config(str(ALEMBIC_INI_FILE))
        # Путь к миграциям относительно расположения alembic.ini
        # При запуске из корня проекта это src/sales_assistant/db/migrations
        alembic_cfg.set_main_option(
            "script_location",
            str(Path(__file__).parent / "db" / "migrations")
        )
        command.upgrade(alembic_cfg, "head")
    else:
        print("Warning: alembic.ini not found, skipping migrations.")

    # Запуск GUI
    app = QApplication(sys.argv)
    app.setApplicationName("SalesAssistant")

    # Применяем тему
    theme = get_setting("theme", "classic")
    apply_theme(app, theme)

    # Главное окно
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()