import sys
from pathlib import Path

# Добавляем папку src в пути импорта
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sales_assistant.app import main

if __name__ == "__main__":
    main()