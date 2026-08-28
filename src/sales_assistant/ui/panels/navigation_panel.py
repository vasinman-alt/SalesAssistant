# -*- coding: utf-8 -*-
"""
Панель навигации: список компаний, поиск, фильтр по региону.
"""
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QComboBox, QLabel, QMenu, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from sales_assistant.db.engine import SessionLocal
from sales_assistant.services.company_service import CompanyService
from sales_assistant.ui.utils.dialogs import show_error_message

# Полный список регионов РФ с кодами КЛАДР (тот же, что в search_dialog)
REGIONS = [
    ("01", "Республика Адыгея"),
    ("02", "Республика Башкортостан"),
    ("03", "Республика Бурятия"),
    ("04", "Республика Алтай"),
    ("05", "Республика Дагестан"),
    ("06", "Республика Ингушетия"),
    ("07", "Кабардино-Балкарская Республика"),
    ("08", "Республика Калмыкия"),
    ("09", "Карачаево-Черкесская Республика"),
    ("10", "Республика Карелия"),
    ("11", "Республика Коми"),
    ("12", "Республика Марий Эл"),
    ("13", "Республика Мордовия"),
    ("14", "Республика Саха (Якутия)"),
    ("15", "Республика Северная Осетия-Алания"),
    ("16", "Республика Татарстан"),
    ("17", "Республика Тыва"),
    ("18", "Удмуртская Республика"),
    ("19", "Республика Хакасия"),
    ("20", "Чеченская Республика"),
    ("21", "Чувашская Республика"),
    ("22", "Алтайский край"),
    ("23", "Краснодарский край"),
    ("24", "Красноярский край"),
    ("25", "Приморский край"),
    ("26", "Ставропольский край"),
    ("27", "Хабаровский край"),
    ("28", "Амурская область"),
    ("29", "Архангельская область и Ненецкий АО"),
    ("30", "Астраханская область"),
    ("31", "Белгородская область"),
    ("32", "Брянская область"),
    ("33", "Владимирская область"),
    ("34", "Волгоградская область"),
    ("35", "Вологодская область"),
    ("36", "Воронежская область"),
    ("37", "Ивановская область"),
    ("38", "Иркутская область"),
    ("39", "Калининградская область"),
    ("40", "Калужская область"),
    ("41", "Камчатский край"),
    ("42", "Кемеровская область"),
    ("43", "Кировская область"),
    ("44", "Костромская область"),
    ("45", "Курганская область"),
    ("46", "Курская область"),
    ("47", "Ленинградская область"),
    ("48", "Липецкая область"),
    ("49", "Магаданская область"),
    ("50", "Московская область"),
    ("51", "Мурманская область"),
    ("52", "Нижегородская область"),
    ("53", "Новгородская область"),
    ("54", "Новосибирская область"),
    ("55", "Омская область"),
    ("56", "Оренбургская область"),
    ("57", "Орловская область"),
    ("58", "Пензенская область"),
    ("59", "Пермский край"),
    ("60", "Псковская область"),
    ("61", "Ростовская область"),
    ("62", "Рязанская область"),
    ("63", "Самарская область"),
    ("64", "Саратовская область"),
    ("65", "Сахалинская область"),
    ("66", "Свердловская область"),
    ("67", "Смоленская область"),
    ("68", "Тамбовская область"),
    ("69", "Тверская область"),
    ("70", "Томская область"),
    ("71", "Тульская область"),
    ("72", "Тюменская область"),
    ("73", "Ульяновская область"),
    ("74", "Челябинская область"),
    ("75", "Забайкальский край"),
    ("76", "Ярославская область"),
    ("77", "г. Москва"),
    ("78", "г. Санкт-Петербург"),
    ("79", "Еврейская автономная область"),
    ("86", "Ханты-Мансийский АО — Югра"),
    ("87", "Чукотский АО"),
    ("89", "Ямало-Ненецкий АО"),
    ("91", "Республика Крым"),
    ("92", "г. Севастополь"),
]


class NavigationPanel(QWidget):
    company_selected = Signal(uuid.UUID)
    add_company_requested = Signal()
    search_requested = Signal()

    def __init__(self, current_user_id: uuid.UUID, parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.service = CompanyService(current_user_id)
        self._init_ui()
        self._load_companies()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по названию или ИНН")
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)

        btn_add = QPushButton("+ Компания")
        btn_add.clicked.connect(self.add_company_requested.emit)
        layout.addWidget(btn_add)

        btn_search = QPushButton("🔍 Поиск предприятий")
        btn_search.clicked.connect(self.search_requested.emit)
        layout.addWidget(btn_search)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Регион:"))
        self.region_combo = QComboBox()
        self.region_combo.addItem("Все регионы", "")
        for code, name in REGIONS:
            self.region_combo.addItem(f"{code} - {name}", code)
        self.region_combo.currentIndexChanged.connect(self._on_region_changed)
        filter_layout.addWidget(self.region_combo)
        layout.addLayout(filter_layout)

        self.company_list = QListWidget()
        self.company_list.itemClicked.connect(self._on_item_clicked)
        self.company_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.company_list.customContextMenuRequested.connect(self._company_context_menu)
        layout.addWidget(self.company_list)

    def _load_companies(self, search_query: str = "", region_code: str = ""):
        with SessionLocal() as session:
            try:
                if search_query.strip():
                    companies = self.service.search(session, search_query.strip())
                else:
                    companies = self.service.get_active(session)
                if region_code:
                    companies = [c for c in companies if c.region and c.region.code == region_code]
            finally:
                session.close()

        self.company_list.clear()
        for company in companies:
            item = QListWidgetItem(company.display_name or company.name)
            item.setData(Qt.UserRole, str(company.id))
            self.company_list.addItem(item)

    def _on_search(self, text: str):
        self._load_companies(text, "")

    def _on_region_changed(self, index):
        if not self.search_edit.text().strip():
            region = self.region_combo.currentData() or ""
            self._load_companies("", region)

    def _on_item_clicked(self, item: QListWidgetItem):
        company_id = uuid.UUID(item.data(Qt.UserRole))
        self.company_selected.emit(company_id)

    def _company_context_menu(self, pos):
        item = self.company_list.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        archive_action = menu.addAction("Архивировать компанию")
        action = menu.exec(self.company_list.viewport().mapToGlobal(pos))
        if action == archive_action:
            self._archive_company(item)

    def _archive_company(self, item: QListWidgetItem):
        company_id = uuid.UUID(item.data(Qt.UserRole))
        company_name = item.text()
        reply = QMessageBox.question(
            self, "Архивация",
            f"Архивировать компанию '{company_name}'?\nОна будет скрыта из общего списка.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with SessionLocal() as session:
                try:
                    self.service.archive(session, company_id)
                    session.commit()
                    self._load_companies(self.search_edit.text(), self.region_combo.currentData())
                except Exception as e:
                    show_error_message(self, "Ошибка архивации", str(e))