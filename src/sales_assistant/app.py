# -*- coding: utf-8 -*-
"""
Точка входа в приложение.
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from sales_assistant.config.settings import get_setting
from sales_assistant.config.paths import ensure_data_dirs, ALEMBIC_INI_FILE
from sales_assistant.ui.main_window import MainWindow
from sales_assistant.ui.themes.theme_manager import apply_theme
from sales_assistant.utils import logging_config

def main():
    # 0. Настройка логирования раньше всего
    logging_config.setup()

    # 1. Подготовка данных и миграции
    ensure_data_dirs()
    if ALEMBIC_INI_FILE.exists():
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(str(ALEMBIC_INI_FILE))
        alembic_cfg.set_main_option("script_location", str(Path(__file__).parent / "db" / "migrations"))
        command.upgrade(alembic_cfg, "head")

    # 2. Запуск GUI
    app = QApplication(sys.argv)
    app.setApplicationName("SalesAssistant")

    theme = get_setting("theme", "classic")
    apply_theme(app, theme)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()