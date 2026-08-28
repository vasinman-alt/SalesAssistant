# -*- coding: utf-8 -*-
"""
Диалог поиска предприятий (источник: Checko).
"""
import uuid
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QCheckBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QGroupBox, QFormLayout, QMenu, QApplication
)
from PySide6.QtCore import Qt, Signal, QThread, QObject, Slot
from PySide6.QtGui import QColor, QAction, QKeySequence

from sales_assistant.search.service import SearchService
from sales_assistant.search.checko_client import CheckoClient
from sales_assistant.db.engine import SessionLocal
from sales_assistant.config.settings import get_setting, set_setting
from sales_assistant.ui.utils.dialogs import show_error_message

logger = logging.getLogger(__name__)

REGIONS = [
    ("01", "Республика Адыгея"), ("02", "Республика Башкортостан"),
    ("03", "Республика Бурятия"), ("04", "Республика Алтай"),
    ("05", "Республика Дагестан"), ("06", "Республика Ингушетия"),
    ("07", "Кабардино-Балкарская Республика"), ("08", "Республика Калмыкия"),
    ("09", "Карачаево-Черкесская Республика"), ("10", "Республика Карелия"),
    ("11", "Республика Коми"), ("12", "Республика Марий Эл"),
    ("13", "Республика Мордовия"), ("14", "Республика Саха (Якутия)"),
    ("15", "Республика Северная Осетия-Алания"), ("16", "Республика Татарстан"),
    ("17", "Республика Тыва"), ("18", "Удмуртская Республика"),
    ("19", "Республика Хакасия"), ("20", "Чеченская Республика"),
    ("21", "Чувашская Республика"), ("22", "Алтайский край"),
    ("23", "Краснодарский край"), ("24", "Красноярский край"),
    ("25", "Приморский край"), ("26", "Ставропольский край"),
    ("27", "Хабаровский край"), ("28", "Амурская область"),
    ("29", "Архангельская область и Ненецкий АО"), ("30", "Астраханская область"),
    ("31", "Белгородская область"), ("32", "Брянская область"),
    ("33", "Владимирская область"), ("34", "Волгоградская область"),
    ("35", "Вологодская область"), ("36", "Воронежская область"),
    ("37", "Ивановская область"), ("38", "Иркутская область"),
    ("39", "Калининградская область"), ("40", "Калужская область"),
    ("41", "Камчатский край"), ("42", "Кемеровская область"),
    ("43", "Кировская область"), ("44", "Костромская область"),
    ("45", "Курганская область"), ("46", "Курская область"),
    ("47", "Ленинградская область"), ("48", "Липецкая область"),
    ("49", "Магаданская область"), ("50", "Московская область"),
    ("51", "Мурманская область"), ("52", "Нижегородская область"),
    ("53", "Новгородская область"), ("54", "Новосибирская область"),
    ("55", "Омская область"), ("56", "Оренбургская область"),
    ("57", "Орловская область"), ("58", "Пензенская область"),
    ("59", "Пермский край"), ("60", "Псковская область"),
    ("61", "Ростовская область"), ("62", "Рязанская область"),
    ("63", "Самарская область"), ("64", "Саратовская область"),
    ("65", "Сахалинская область"), ("66", "Свердловская область"),
    ("67", "Смоленская область"), ("68", "Тамбовская область"),
    ("69", "Тверская область"), ("70", "Томская область"),
    ("71", "Тульская область"), ("72", "Тюменская область"),
    ("73", "Ульяновская область"), ("74", "Челябинская область"),
    ("75", "Забайкальский край"), ("76", "Ярославская область"),
    ("77", "г. Москва"), ("78", "г. Санкт-Петербург"),
    ("79", "Еврейская автономная область"), ("86", "Ханты-Мансийский АО — Югра"),
    ("87", "Чукотский АО"), ("89", "Ямало-Ненецкий АО"),
    ("91", "Республика Крым"), ("92", "г. Севастополь"),
]


class NumericTableWidgetItem(QTableWidgetItem):
    """Элемент таблицы, сравнивающий числа, а не строки."""
    def __init__(self, value: str, number: float):
        super().__init__(value)
        self.number = number

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.number < other.number
        return super().__lt__(other)


class FinanceWorker(QObject):
    finished = Signal()
    progress = Signal(int)
    error = Signal(str)

    def __init__(self, service: SearchService, results: list):
        super().__init__()
        self.service = service
        self.results = results

    @Slot()
    def run(self):
        try:
            total = len(self.results)
            for idx, r in enumerate(self.results, 1):
                r['revenue'] = self.service.fetch_finances_for(r)
                self.progress.emit(idx)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class SearchDialog(QDialog):
    company_created = Signal()

    def __init__(self, current_user_id: uuid.UUID, parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        checko_key = get_setting("checko_api_key", "")
        self.service = SearchService(current_user_id, checko_api_key=checko_key)
        self.setWindowTitle("Поиск предприятий (Checko)")
        self.resize(1000, 700)
        self._init_ui()
        self._load_regions()
        self.worker = None
        self.thread = None
        self.results = []

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Фильтры
        filters_group = QGroupBox("Фильтры")
        form = QFormLayout(filters_group)

        self.query_edit = QLineEdit()
        self.query_edit.setPlaceholderText("Название, ИНН или ОГРН (мин. 4 симв.)")
        form.addRow("Запрос:", self.query_edit)

        self.region_combo = QComboBox()
        form.addRow("Регион:", self.region_combo)

        self.okved_edit = QLineEdit()
        self.okved_edit.setPlaceholderText("Код ОКВЭД (например, 47.11)")
        form.addRow("ОКВЭД:", self.okved_edit)

        self.active_check = QCheckBox("Только действующие")
        self.active_check.setChecked(True)
        form.addRow("", self.active_check)

        self.load_finances_check = QCheckBox("Загрузить обороты (расходует лимит, может замедлить)")
        self.load_finances_check.setChecked(False)
        form.addRow("", self.load_finances_check)

        layout.addWidget(filters_group)

        # API-ключ
        api_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit(get_setting("checko_api_key", ""))
        self.api_key_edit.setPlaceholderText("API-ключ Checko")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        btn_save_key = QPushButton("Сохранить ключ")
        btn_save_key.clicked.connect(self._save_api_key)
        api_layout.addWidget(self.api_key_edit)
        api_layout.addWidget(btn_save_key)
        layout.addLayout(api_layout)

        # Кнопка поиска
        btn_search = QPushButton("Искать")
        btn_search.clicked.connect(self._on_search)
        layout.addWidget(btn_search)

        # Прогресс-бар для обогащения
        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Название", "ИНН", "КПП", "Регион", "Статус", "ОКВЭД", "Оборот, млн"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._table_context_menu)
        self.table.keyPressEvent = self._table_key_press_event
        layout.addWidget(self.table)

        # Кнопка добавления выбранных
        btn_add_selected = QPushButton("Добавить выбранные компании в базу")
        btn_add_selected.clicked.connect(self._create_multiple_companies)
        layout.addWidget(btn_add_selected)

    def _load_regions(self):
        self.region_combo.addItem("Все регионы", "")
        for code, name in REGIONS:
            self.region_combo.addItem(f"{code} - {name}", code)

    def _save_api_key(self):
        key = self.api_key_edit.text().strip()
        set_setting("checko_api_key", key)
        self.service.checko = CheckoClient(key) if key else None
        QMessageBox.information(self, "Ключ сохранён", "API-ключ Checko сохранён.")

    def _on_search(self):
        query = self.query_edit.text().strip()
        region_code = self.region_combo.currentData() or ""
        only_active = self.active_check.isChecked() if self.active_check.isChecked() else None
        okved = self.okved_edit.text().strip()
        load_finances = self.load_finances_check.isChecked()

        # Разрешён поиск только по ОКВЭД без названия
        if not query and not okved:
            QMessageBox.warning(self, "Пустой запрос", "Введите название, ИНН или код ОКВЭД.")
            return

        # Если название/ИНН не указан, а ОКВЭД указан, ищем по ОКВЭД
        by = ""
        if not query and okved:
            query = okved
            by = "okved"
            okved = ""  # при by=okved не передаём отдельный фильтр

        try:
            if not self.service.checko:
                raise Exception("Не задан API-ключ Checko.")

            self.results = self.service.search_online(
                query=query,
                region_code=region_code,
                okved=okved,
                only_active=only_active,
                by=by,
            )
            self._populate_table()

            if load_finances and self.results:
                self._start_finance_enrichment()

        except Exception as e:
            show_error_message(self, "Ошибка поиска", str(e))

    def _populate_table(self):
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        regions_dict = {code: name for code, name in REGIONS}
        for row_idx, r in enumerate(self.results):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(r.get('name', '')))
            self.table.setItem(row_idx, 1, QTableWidgetItem(r.get('inn', '')))
            self.table.setItem(row_idx, 2, QTableWidgetItem(r.get('kpp', '')))
            region_code = r.get('region_code', '')
            region_name = regions_dict.get(region_code, region_code)
            self.table.setItem(row_idx, 3, QTableWidgetItem(region_name))
            self.table.setItem(row_idx, 4, QTableWidgetItem(r.get('status', '')))
            self.table.setItem(row_idx, 5, QTableWidgetItem(r.get('okved_main', '')))
            revenue = r.get('revenue', 0) or 0
            revenue_str = f"{float(revenue)/1e6:.2f}" if revenue else ""
            self.table.setItem(row_idx, 6, NumericTableWidgetItem(revenue_str, float(revenue)))
            # Сохраняем данные строки
            self.table.item(row_idx, 0).setData(Qt.UserRole, r)
        self.table.setSortingEnabled(True)

    def _start_finance_enrichment(self):
        self.progress_label.setText("Загрузка оборотов...")
        self.thread = QThread()
        self.worker = FinanceWorker(self.service, self.results)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_enrich_progress)
        self.worker.finished.connect(self._on_enrich_finished)
        self.worker.error.connect(self._on_enrich_error)
        self.thread.start()

    @Slot(int)
    def _on_enrich_progress(self, count):
        self.progress_label.setText(f"Загружено оборотов: {count}/{len(self.results)}")

    @Slot()
    def _on_enrich_finished(self):
        self.progress_label.setText("Обороты загружены.")
        self._populate_table()
        self.thread.quit()
        self.thread.wait()

    @Slot(str)
    def _on_enrich_error(self, msg):
        self.progress_label.setText("Ошибка загрузки оборотов.")
        self.thread.quit()
        self.thread.wait()

    def _table_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        copy_action = QAction("Копировать текст ячейки", self)
        copy_action.triggered.connect(lambda: self._copy_selected_text())
        menu.addAction(copy_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _copy_selected_text(self):
        selected = self.table.selectedRanges()
        if selected:
            texts = []
            for r in selected:
                for row in range(r.topRow(), r.bottomRow()+1):
                    row_texts = []
                    for col in range(r.leftColumn(), r.rightColumn()+1):
                        item = self.table.item(row, col)
                        if item: row_texts.append(item.text())
                    if row_texts: texts.append('\t'.join(row_texts))
            if texts: QApplication.clipboard().setText('\n'.join(texts))
        else:
            current = self.table.currentItem()
            if current: QApplication.clipboard().setText(current.text())

    def _table_key_press_event(self, event):
        if event.matches(QKeySequence.Copy):
            self._copy_selected_text()
        else:
            QTableWidget.keyPressEvent(self.table, event)

    def _create_multiple_companies(self):
        selected_rows = set(idx.row() for idx in self.table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Не выбрано", "Выделите хотя бы одну компанию.")
            return
        count = 0
        with SessionLocal() as session:
            try:
                for row in selected_rows:
                    data = self.table.item(row, 0).data(Qt.UserRole)
                    if data:
                        self.service.create_and_enrich_company(session, data)
                        count += 1
                session.commit()
                QMessageBox.information(self, "Успех", f"Добавлено компаний: {count}")
                self.company_created.emit()
            except Exception as e:
                session.rollback()
                show_error_message(self, "Ошибка добавления", str(e))