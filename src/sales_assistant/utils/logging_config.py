# -*- coding: utf-8 -*-
"""
Настройка логирования для всего приложения.
"""
import logging
import sys
from pathlib import Path

def setup():
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Можно добавить FileHandler, если нужно писать в файл
        ]
    )
    # Отключаем слишком подробное логирование от библиотек
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)