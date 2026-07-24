# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.ui.panels.company_card.

Виджет карточки компании (просмотр).
"""
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QGroupBox, QListWidget,
    QListWidgetItem
)
from sqlalchemy.orm import Session

from sales_assistant.db.engine import SessionLocal
from sales_assistant.services.company_service import CompanyService
from sales_assistant.services.contact_service import ContactService


class CompanyCardWidget(QWidget):
    """Виджет для просмотра карточки компании."""

    def __init__(self, current_user_id: uuid.UUID, parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.company_service = CompanyService(current_user_id)
        self.contact_service = ContactService(current_user_id)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Основная информация
        info_group = QGroupBox("Общая информация")
        form = QFormLayout()
        self.lbl_name = QLabel()
        self.lbl_inn = QLabel()
        self.lbl_region = QLabel()
        self.lbl_address = QLabel()
        self.lbl_website = QLabel()
        self.lbl_comment = QLabel()

        form.addRow("Название:", self.lbl_name)
        form.addRow("ИНН:", self.lbl_inn)
        form.addRow("Регион:", self.lbl_region)
        form.addRow("Адрес:", self.lbl_address)
        form.addRow("Сайт:", self.lbl_website)
        form.addRow("Комментарий:", self.lbl_comment)
        info_group.setLayout(form)
        layout.addWidget(info_group)

        # Контакты
        contacts_group = QGroupBox("Контакты")
        self.contacts_list = QListWidget()
        contacts_layout = QVBoxLayout()
        contacts_layout.addWidget(self.contacts_list)
        contacts_group.setLayout(contacts_layout)
        layout.addWidget(contacts_group)

        # Растяжение
        layout.addStretch()

    def load_company(self, company_id: uuid.UUID):
        """Загрузить данные компании и отобразить."""
        with SessionLocal() as session:
            try:
                company = self.company_service.get_by_id(session, company_id)
                if not company:
                    self._clear()
                    return

                self.lbl_name.setText(company.name)
                self.lbl_inn.setText(company.inn or "")
                self.lbl_region.setText(company.region.name if company.region else "")
                self.lbl_address.setText(company.actual_address or company.legal_address or "")
                self.lbl_website.setText(company.website or "")
                self.lbl_comment.setText(company.comment or "")

                # Контакты
                contacts = self.contact_service.get_by_company(session, company_id)
                self.contacts_list.clear()
                for c in contacts:
                    item_text = f"{c.full_name or 'Без имени'} ({c.contact_type})"
                    item = QListWidgetItem(item_text)
                    self.contacts_list.addItem(item)

            finally:
                session.close()

    def _clear(self):
        self.lbl_name.clear()
        self.lbl_inn.clear()
        self.lbl_region.clear()
        self.lbl_address.clear()
        self.lbl_website.clear()
        self.lbl_comment.clear()
        self.contacts_list.clear()