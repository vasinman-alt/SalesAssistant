"""
Однократный скрипт для добавления заголовков во все __init__.py проекта.
Добавляет:
- # -*- coding: utf-8 -*-
- docstring с полным именем пакета.

Запускать из корня SalesAssistant.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src", "sales_assistant")
TESTS_DIR = os.path.join(ROOT_DIR, "tests")

HEADER_TEMPLATE = '''# -*- coding: utf-8 -*-
"""
Пакет {dotted_name}.
"""
'''

def dotted_name_from_path(file_path, base_dir):
    """Вычисляет dotted имя пакета из полного пути к __init__.py"""
    rel = os.path.relpath(file_path, base_dir)
    parts = rel.replace(os.sep, '.').split('.')
    # Убираем последний '__init__'
    if parts[-1] == '__init__':
        parts = parts[:-1]
    return '.'.join(parts)

def process_init(file_path, dotted_name):
    with open(file_path, 'r+', encoding='utf-8') as f:
        content = f.read()
        # Проверка, что файл пуст или не содержит уже заголовок
        if content.strip().startswith('# -*- coding: utf-8 -*-'):
            print(f"⏭️  Пропущен (уже есть заголовок): {file_path}")
            return

        f.seek(0)
        f.truncate()
        header = HEADER_TEMPLATE.format(dotted_name=dotted_name)
        f.write(header + content.lstrip('\n'))

def main():
    for base_dir, base_dotted in [(SRC_DIR, "sales_assistant"), (TESTS_DIR, "tests")]:
        if not os.path.isdir(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            if '__init__.py' in files:
                init_path = os.path.join(root, '__init__.py')
                # dotted_name: база + относительный путь внутри пакета
                rel_dir = os.path.relpath(root, base_dir)
                if rel_dir == '.':
                    full_dotted = base_dotted
                else:
                    full_dotted = base_dotted + '.' + rel_dir.replace(os.sep, '.')
                process_init(init_path, full_dotted)

if __name__ == '__main__':
    main()
    print("Готово. Все __init__.py обработаны.")