# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.ui.panels.navigation_panel.

Панель навигации: поиск и список компаний.
"""
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton
)
from PySide6.QtCore import Signal
from sqlalchemy.orm import Session

from sales_assistant.db.engine import SessionLocal
from sales_assistant.services.company_service import CompanyService


class NavigationPanel(QWidget):
    """Панель со списком компаний и поиском."""

    company_selected = Signal(uuid.UUID)  # выбранная компания
    add_company_requested = Signal()      # запрос на создание новой

    def __init__(self, current_user_id: uuid.UUID, parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.service = CompanyService(current_user_id)
        self._init_ui()
        self._load_companies()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Строка поиска
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по названию или ИНН")
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)

        # Кнопка "Добавить компанию"
        btn_add = QPushButton("+ Компания")
        btn_add.clicked.connect(self.add_company_requested.emit)
        layout.addWidget(btn_add)

        # Список компаний
        self.company_list = QListWidget()
        self.company_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.company_list)

    def _load_companies(self, search_query: str = ""):
        """Загрузить список компаний из БД и отобразить."""
        with SessionLocal() as session:
            try:
                if search_query.strip():
                    companies = self.service.search(session, search_query.strip())
                else:
                    companies = self.service.get_active(session)
            finally:
                session.close()

        self.company_list.clear()
        for company in companies:
            item = QListWidgetItem(company.name)
            item.setData(1, str(company.id))  # скрытые данные – UUID
            self.company_list.addItem(item)

    def _on_search(self, text: str):
        self._load_companies(text)

    def _on_item_clicked(self, item: QListWidgetItem):
        company_id = uuid.UUID(item.data(1))
        self.company_selected.emit(company_id)