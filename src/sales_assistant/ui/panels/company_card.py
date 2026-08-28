# -*- coding: utf-8 -*-
"""
Виджет карточки компании с вкладками: общая информация, история, задачи, документы.
"""
import uuid
import os
import locale
import logging
from datetime import datetime, timezone
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QGroupBox, QListWidget,
    QListWidgetItem, QTabWidget, QPushButton, QMessageBox,
    QDialog, QLineEdit, QTextEdit, QComboBox, QDateTimeEdit, QDialogButtonBox,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu,
    QAbstractItemView, QCheckBox, QInputDialog
)
from PySide6.QtCore import Qt, QDateTime, QUrl, Signal
from PySide6.QtGui import QDesktopServices

from sales_assistant.db.engine import SessionLocal
from sales_assistant.services.company_service import CompanyService
from sales_assistant.services.contact_service import ContactService
from sales_assistant.services.interaction_service import InteractionService
from sales_assistant.services.task_service import TaskService
from sales_assistant.services.document_service import DocumentService
from sales_assistant.db.models.contact import Contact, ContactPhone, ContactEmail
from sales_assistant.ui.utils.dialogs import show_error_message
from sales_assistant.config.settings import get_node_id

logger = logging.getLogger(__name__)


class CompanyCardWidget(QWidget):
    file_preview_requested = Signal(str)

    def __init__(self, current_user_id: uuid.UUID, parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.company_service = CompanyService(current_user_id)
        self.contact_service = ContactService(current_user_id)
        self.interaction_service = InteractionService(current_user_id)
        self.task_service = TaskService(current_user_id)
        self.document_service = DocumentService(current_user_id)
        self.company_id = None
        self._init_ui()

    # --------------------------------------------------------------
    # UI construction
    # --------------------------------------------------------------
    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # Вкладка "Общая информация"
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)

        info_group = QGroupBox("Общая информация")
        form = QFormLayout()

        # Название (альтернативное)
        self.lbl_name = QLabel()
        self.btn_edit_display = QPushButton("✎")
        self.btn_edit_display.setFixedWidth(30)
        self.btn_edit_display.clicked.connect(self._edit_display_name)
        name_row = QHBoxLayout()
        name_row.addWidget(self.lbl_name)
        name_row.addWidget(self.btn_edit_display)
        form.addRow("Название:", name_row)

        # Юридическое название
        self.lbl_legal_name = QLabel()
        self.btn_edit_legal = QPushButton("✎")
        self.btn_edit_legal.setFixedWidth(30)
        self.btn_edit_legal.clicked.connect(self._edit_legal_name)
        legal_row = QHBoxLayout()
        legal_row.addWidget(self.lbl_legal_name)
        legal_row.addWidget(self.btn_edit_legal)
        form.addRow("Юр. название:", legal_row)

        self.lbl_inn = QLabel()
        self.lbl_region = QLabel()
        self.lbl_address = QLabel()

        # Сайт
        self.lbl_website = QLabel()
        self.lbl_website.setTextFormat(Qt.RichText)
        self.lbl_website.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.lbl_website.setOpenExternalLinks(True)
        self.btn_edit_website = QPushButton("✎")
        self.btn_edit_website.setFixedWidth(30)
        self.btn_edit_website.clicked.connect(self._edit_website)
        website_row = QHBoxLayout()
        website_row.addWidget(self.lbl_website)
        website_row.addWidget(self.btn_edit_website)

        self.lbl_comment = QLabel()
        form.addRow("ИНН:", self.lbl_inn)
        form.addRow("Регион:", self.lbl_region)
        form.addRow("Адрес:", self.lbl_address)
        form.addRow("Сайт:", website_row)
        form.addRow("Комментарий:", self.lbl_comment)

        # Телефоны (быстрый ввод)
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Телефоны через запятую")
        self.phone_edit.editingFinished.connect(self._save_phones)
        form.addRow("Телефоны:", self.phone_edit)

        info_group.setLayout(form)
        info_layout.addWidget(info_group)

        # Контакты
        contacts_group = QGroupBox("Контакты")
        contacts_layout = QVBoxLayout()
        self.contacts_list = QListWidget()
        self.contacts_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.contacts_list.customContextMenuRequested.connect(self._contact_context_menu)
        contacts_layout.addWidget(self.contacts_list)
        btn_add_contact = QPushButton("+ Добавить контакт")
        btn_add_contact.clicked.connect(self._add_contact_dialog)
        contacts_layout.addWidget(btn_add_contact)
        contacts_group.setLayout(contacts_layout)
        info_layout.addWidget(contacts_group)

        self.tabs.addTab(info_tab, "Общее")

        # Вкладка "История"
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        btn_add_interaction = QPushButton("+ Добавить взаимодействие")
        btn_add_interaction.clicked.connect(self._add_interaction_dialog)
        history_layout.addWidget(btn_add_interaction)
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._show_interaction_detail)
        history_layout.addWidget(self.history_list)
        self.tabs.addTab(history_tab, "История")

        # Вкладка "Задачи"
        tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(tasks_tab)
        btn_add_task = QPushButton("+ Добавить задачу")
        btn_add_task.clicked.connect(self._add_task_dialog)
        tasks_layout.addWidget(btn_add_task)
        self.tasks_list = QListWidget()
        self.tasks_list.itemDoubleClicked.connect(self._toggle_task_status)
        tasks_layout.addWidget(self.tasks_list)
        self.tabs.addTab(tasks_tab, "Задачи")

        # Вкладка "Документы"
        docs_tab = QWidget()
        docs_layout = QVBoxLayout(docs_tab)
        btn_add_doc = QPushButton("+ Добавить документ")
        btn_add_doc.clicked.connect(self._add_document_dialog)
        docs_layout.addWidget(btn_add_doc)
        self.docs_tree = QTreeWidget()
        self.docs_tree.setColumnCount(5)
        self.docs_tree.setHeaderLabels(["Имя файла", "Комментарий", "Размер", "Дата создания", "Дата изменения"])
        self.docs_tree.setAlternatingRowColors(True)
        self.docs_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.docs_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.docs_tree.customContextMenuRequested.connect(self._on_doc_context_menu)
        self.docs_tree.itemClicked.connect(self._on_doc_single_click)
        self.docs_tree.itemDoubleClicked.connect(self._on_doc_double_clicked)
        header = self.docs_tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        docs_layout.addWidget(self.docs_tree)
        self.tabs.addTab(docs_tab, "Документы")

        layout.addWidget(self.tabs)

    # --------------------------------------------------------------
    # Data loading
    # --------------------------------------------------------------
    def load_company(self, company_id: uuid.UUID):
        self.company_id = company_id
        with SessionLocal() as session:
            try:
                company = self.company_service.get_by_id(session, company_id)
                if not company:
                    self._clear()
                    return

                self.lbl_name.setText(company.display_name or company.name)
                self.lbl_legal_name.setText(company.legal_name or "")
                self.lbl_inn.setText(company.inn or "")
                self.lbl_region.setText(company.region.name if company.region else "")
                self.lbl_address.setText(company.actual_address or company.legal_address or "")
                if company.website:
                    self.lbl_website.setText(f"<a href='{company.website}'>{company.website}</a>")
                else:
                    self.lbl_website.setText("")
                self.lbl_comment.setText(company.comment or "")

                contacts = self.contact_service.get_by_company(session, company_id)
                phones = []
                for c in contacts:
                    for p in c.phones:
                        phones.append(p.phone)
                self.phone_edit.setText(", ".join(phones))

                self.contacts_list.clear()
                for c in contacts:
                    self._add_contact_to_list(c)

                interactions = self.interaction_service.get_by_company(session, company_id)
                self.history_list.clear()
                for i in interactions:
                    item_text = f"{i.event_date.strftime('%d.%m.%Y %H:%M')} - {i.subject} ({i.type})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, i.id)
                    self.history_list.addItem(item)

                tasks = self.task_service.get_by_company(session, company_id)
                self.tasks_list.clear()
                for t in tasks:
                    due_str = f"до {t.due_date.strftime('%d.%m.%Y %H:%M')}" if t.due_date else "нет срока"
                    item_text = f"[{'✓' if t.status == 'done' else ' '}] {t.title} ({due_str})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, t.id)
                    self.tasks_list.addItem(item)

                docs = self.document_service.get_by_entity(session, "company", company_id)
                self.docs_tree.clear()
                for d in docs:
                    file_path = d.file_path
                    exists = os.path.exists(file_path)
                    size_str = ctime_str = mtime_str = "—"
                    if exists:
                        stat = os.stat(file_path)
                        size_str = locale.format_string("%.1f KB", stat.st_size / 1024, grouping=True)
                        ctime_str = datetime.fromtimestamp(stat.st_ctime).strftime("%d.%m.%Y %H:%M")
                        mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
                    item = QTreeWidgetItem([d.original_name, d.comment or "", size_str, ctime_str, mtime_str])
                    item.setData(0, Qt.UserRole, file_path)
                    item.setData(0, Qt.UserRole + 1, d.id)
                    if not exists:
                        item.setForeground(0, Qt.gray)
                        item.setToolTip(0, "Файл не найден по указанному пути")
                    self.docs_tree.addTopLevelItem(item)
            finally:
                session.close()

    def _clear(self):
        self.lbl_name.clear()
        self.lbl_legal_name.clear()
        self.lbl_inn.clear()
        self.lbl_region.clear()
        self.lbl_address.clear()
        self.lbl_website.clear()
        self.lbl_comment.clear()
        self.phone_edit.clear()
        self.contacts_list.clear()
        self.history_list.clear()
        self.tasks_list.clear()
        self.docs_tree.clear()

    # --------------------------------------------------------------
    # Editing
    # --------------------------------------------------------------
    def _edit_display_name(self):
        if not self.company_id: return
        new_name, ok = QInputDialog.getText(self, "Альтернативное название", "Введите короткое название:", text=self.lbl_name.text())
        if ok and new_name.strip():
            with SessionLocal() as session:
                try:
                    self.company_service.update_display_name(session, self.company_id, new_name.strip())
                    session.commit()
                    self.lbl_name.setText(new_name.strip())
                except Exception as e:
                    show_error_message(self, "Ошибка", str(e))

    def _edit_legal_name(self):
        if not self.company_id: return
        current = self.lbl_legal_name.text()
        new_name, ok = QInputDialog.getText(self, "Юридическое название", "Введите полное юридическое название:", text=current)
        if ok and new_name.strip():
            with SessionLocal() as session:
                try:
                    self.company_service.update_legal_name(session, self.company_id, new_name.strip())
                    session.commit()
                    self.lbl_legal_name.setText(new_name.strip())
                except Exception as e:
                    show_error_message(self, "Ошибка", str(e))

    def _edit_website(self):
        if not self.company_id: return
        current = self.lbl_website.text()
        if current.startswith("<a href="):
            import re
            match = re.search(r"href='([^']*)'", current)
            if match: current = match.group(1)
            else: current = ""
        new_url, ok = QInputDialog.getText(self, "Сайт", "Введите URL сайта:", text=current)
        if ok and new_url.strip():
            with SessionLocal() as session:
                company = self.company_service.get_by_id(session, self.company_id)
                if company:
                    company.website = new_url.strip()
                    session.commit()
                    self.lbl_website.setText(f"<a href='{new_url}'>{new_url}</a>")

    def _save_phones(self):
        if not self.company_id: return
        phones_text = self.phone_edit.text().strip()
        with SessionLocal() as session:
            try:
                contacts = session.query(Contact).filter(
                    Contact.company_id == self.company_id,
                    Contact.contact_type == 'phone_shared'
                ).all()
                for c in contacts:
                    session.delete(c)
                session.flush()

                if phones_text:
                    contact = Contact(
                        id=uuid.uuid4(),
                        company_id=self.company_id,
                        contact_type='phone_shared',
                        full_name='Основной телефон',
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                        origin_node=get_node_id(),
                        version=1
                    )
                    session.add(contact)
                    session.flush()
                    for phone in phones_text.split(','):
                        phone = phone.strip()
                        if phone:
                            session.add(ContactPhone(id=uuid.uuid4(), contact_id=contact.id, phone=phone))
                session.commit()
                self.load_company(self.company_id)
            except Exception as e:
                session.rollback()
                show_error_message(self, "Ошибка сохранения телефонов", str(e))

    # --------------------------------------------------------------
    # Contact management
    # --------------------------------------------------------------
    def _add_contact_to_list(self, contact):
        phones = []
        for p in contact.phones:
            label = f" ({p.label})" if p.label else ""
            phones.append(f"{p.phone}{label}")
        emails = []
        for e in contact.emails:
            label = f" ({e.label})" if e.label else ""
            emails.append(f"{e.email}{label}")
        details = []
        if phones: details.append("Тел: " + ", ".join(phones))
        if emails: details.append("Email: " + ", ".join(emails))
        details_str = " | ".join(details)
        name = contact.full_name or "Без имени"
        item_text = f"{name} ({contact.contact_type})"
        if details_str:
            item_text += f" – {details_str}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, contact.id)
        self.contacts_list.addItem(item)

    def _add_contact_dialog(self):
        if not self.company_id: return
        dialog = QDialog(self)
        dialog.setWindowTitle("Новый контакт")
        layout = QFormLayout(dialog)

        last_name_edit = QLineEdit()
        first_name_edit = QLineEdit()
        patronymic_edit = QLineEdit()
        position_edit = QLineEdit()
        type_combo = QComboBox()
        type_combo.addItems(["person", "phone_shared", "email_shared", "department", "reception"])

        layout.addRow("Фамилия:", last_name_edit)
        layout.addRow("Имя:", first_name_edit)
        layout.addRow("Отчество:", patronymic_edit)
        layout.addRow("Должность:", position_edit)
        layout.addRow("Тип контакта:", type_combo)

        # Динамические телефоны
        phones_widget = QWidget()
        phones_layout = QVBoxLayout(phones_widget)
        phones_layout.setContentsMargins(0, 0, 0, 0)
        phone_rows = []

        def add_phone_row():
            row = QHBoxLayout()
            phone_edit = QLineEdit()
            phone_edit.setPlaceholderText("+7 900 123-45-67")
            category = QComboBox()
            category.addItems(["мобильный", "рабочий", "личный", "другой"])
            row.addWidget(phone_edit)
            row.addWidget(category)
            phone_rows.append((phone_edit, category))
            phones_layout.addLayout(row)

        add_phone_row()
        btn_add_phone = QPushButton("+")
        btn_add_phone.clicked.connect(add_phone_row)
        phones_layout.addWidget(btn_add_phone)
        layout.addRow("Телефоны:", phones_widget)

        # Динамические email
        emails_widget = QWidget()
        emails_layout = QVBoxLayout(emails_widget)
        emails_layout.setContentsMargins(0, 0, 0, 0)
        email_rows = []

        def add_email_row():
            row = QHBoxLayout()
            email_edit = QLineEdit()
            email_edit.setPlaceholderText("email@example.com")
            category = QComboBox()
            category.addItems(["рабочий", "личный", "другой"])
            row.addWidget(email_edit)
            row.addWidget(category)
            email_rows.append((email_edit, category))
            emails_layout.addLayout(row)

        add_email_row()
        btn_add_email = QPushButton("+")
        btn_add_email.clicked.connect(add_email_row)
        emails_layout.addWidget(btn_add_email)
        layout.addRow("Email:", emails_widget)

        comment_edit = QLineEdit()
        layout.addRow("Комментарий:", comment_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            full_name = f"{last_name_edit.text().strip()} {first_name_edit.text().strip()} {patronymic_edit.text().strip()}".strip()
            contact = Contact(
                id=uuid.uuid4(),
                company_id=self.company_id,
                contact_type=type_combo.currentText(),
                full_name=full_name or None,
                position=position_edit.text().strip() or None,
                comment=comment_edit.text().strip() or None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                origin_node=get_node_id(),
                version=1
            )
            with SessionLocal() as session:
                try:
                    session.add(contact)
                    session.flush()
                    for phone_edit, category in phone_rows:
                        phone = phone_edit.text().strip()
                        if phone:
                            session.add(ContactPhone(id=uuid.uuid4(), contact_id=contact.id, phone=phone, label=category.currentText()))
                    for email_edit, category in email_rows:
                        email = email_edit.text().strip()
                        if email:
                            session.add(ContactEmail(id=uuid.uuid4(), contact_id=contact.id, email=email, label=category.currentText()))
                    session.commit()
                    self.load_company(self.company_id)
                except Exception as e:
                    show_error_message(self, "Ошибка", str(e))

    def _edit_contact_dialog(self, contact_id):
        with SessionLocal() as session:
            contact = session.query(Contact).get(contact_id)
            if not contact: return
            dialog = QDialog(self)
            dialog.setWindowTitle("Редактировать контакт")
            layout = QFormLayout(dialog)

            parts = (contact.full_name or "").split()
            last_name = parts[0] if len(parts) > 0 else ""
            first_name = parts[1] if len(parts) > 1 else ""
            patronymic = parts[2] if len(parts) > 2 else ""

            last_name_edit = QLineEdit(last_name)
            first_name_edit = QLineEdit(first_name)
            patronymic_edit = QLineEdit(patronymic)
            position_edit = QLineEdit(contact.position or "")
            type_combo = QComboBox()
            type_combo.addItems(["person", "phone_shared", "email_shared", "department", "reception"])
            type_combo.setCurrentText(contact.contact_type)

            layout.addRow("Фамилия:", last_name_edit)
            layout.addRow("Имя:", first_name_edit)
            layout.addRow("Отчество:", patronymic_edit)
            layout.addRow("Должность:", position_edit)
            layout.addRow("Тип контакта:", type_combo)

            # Телефоны
            phones_widget = QWidget()
            phones_layout = QVBoxLayout(phones_widget)
            phones_layout.setContentsMargins(0, 0, 0, 0)
            phone_rows = []
            existing_phones = contact.phones or [None]
            for ph in existing_phones:
                row = QHBoxLayout()
                phone_edit = QLineEdit(ph.phone if ph else "")
                phone_edit.setPlaceholderText("+7 900 123-45-67")
                category = QComboBox()
                category.addItems(["мобильный", "рабочий", "личный", "другой"])
                if ph and ph.label: category.setCurrentText(ph.label)
                row.addWidget(phone_edit)
                row.addWidget(category)
                phone_rows.append((phone_edit, category))
                phones_layout.addLayout(row)

            def add_phone_row():
                row = QHBoxLayout()
                phone_edit = QLineEdit()
                phone_edit.setPlaceholderText("+7 900 123-45-67")
                category = QComboBox()
                category.addItems(["мобильный", "рабочий", "личный", "другой"])
                row.addWidget(phone_edit)
                row.addWidget(category)
                phone_rows.append((phone_edit, category))
                phones_layout.addLayout(row)

            btn_add_phone = QPushButton("+")
            btn_add_phone.clicked.connect(add_phone_row)
            phones_layout.addWidget(btn_add_phone)
            layout.addRow("Телефоны:", phones_widget)

            # Email
            emails_widget = QWidget()
            emails_layout = QVBoxLayout(emails_widget)
            emails_layout.setContentsMargins(0, 0, 0, 0)
            email_rows = []
            existing_emails = contact.emails or [None]
            for em in existing_emails:
                row = QHBoxLayout()
                email_edit = QLineEdit(em.email if em else "")
                email_edit.setPlaceholderText("email@example.com")
                category = QComboBox()
                category.addItems(["рабочий", "личный", "другой"])
                if em and em.label: category.setCurrentText(em.label)
                row.addWidget(email_edit)
                row.addWidget(category)
                email_rows.append((email_edit, category))
                emails_layout.addLayout(row)

            def add_email_row():
                row = QHBoxLayout()
                email_edit = QLineEdit()
                email_edit.setPlaceholderText("email@example.com")
                category = QComboBox()
                category.addItems(["рабочий", "личный", "другой"])
                row.addWidget(email_edit)
                row.addWidget(category)
                email_rows.append((email_edit, category))
                emails_layout.addLayout(row)

            btn_add_email = QPushButton("+")
            btn_add_email.clicked.connect(add_email_row)
            emails_layout.addWidget(btn_add_email)
            layout.addRow("Email:", emails_widget)

            comment_edit = QLineEdit(contact.comment or "")
            layout.addRow("Комментарий:", comment_edit)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            if dialog.exec() == QDialog.Accepted:
                try:
                    full_name = f"{last_name_edit.text().strip()} {first_name_edit.text().strip()} {patronymic_edit.text().strip()}".strip()
                    contact.full_name = full_name or None
                    contact.position = position_edit.text().strip() or None
                    contact.contact_type = type_combo.currentText()
                    contact.comment = comment_edit.text().strip() or None
                    contact.updated_at = datetime.now(timezone.utc)

                    session.query(ContactPhone).filter(ContactPhone.contact_id == contact.id).delete()
                    for phone_edit, category in phone_rows:
                        phone = phone_edit.text().strip()
                        if phone:
                            session.add(ContactPhone(id=uuid.uuid4(), contact_id=contact.id, phone=phone, label=category.currentText()))
                    session.query(ContactEmail).filter(ContactEmail.contact_id == contact.id).delete()
                    for email_edit, category in email_rows:
                        email = email_edit.text().strip()
                        if email:
                            session.add(ContactEmail(id=uuid.uuid4(), contact_id=contact.id, email=email, label=category.currentText()))
                    session.commit()
                    self.load_company(self.company_id)
                except Exception as e:
                    show_error_message(self, "Ошибка", str(e))

    def _contact_context_menu(self, pos):
        item = self.contacts_list.itemAt(pos)
        if not item: return
        contact_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")
        action = menu.exec(self.contacts_list.viewport().mapToGlobal(pos))
        if action == delete_action:
            self._delete_contact(contact_id)
        elif action == edit_action:
            self._edit_contact_dialog(contact_id)

    def _delete_contact(self, contact_id):
        with SessionLocal() as session:
            try:
                contact = session.query(Contact).get(contact_id)
                if contact:
                    session.delete(contact)
                    session.commit()
                    self.load_company(self.company_id)
            except Exception as e:
                show_error_message(self, "Ошибка", str(e))

    # --------------------------------------------------------------
    # History
    # --------------------------------------------------------------
    def _add_interaction_dialog(self):
        if not self.company_id: return
        dialog = QDialog(self)
        dialog.setWindowTitle("Новое взаимодействие")
        layout = QFormLayout(dialog)

        type_combo = QComboBox()
        type_combo.addItems(["call", "meeting", "letter", "video", "message", "note"])
        layout.addRow("Тип:", type_combo)

        subject_edit = QLineEdit()
        layout.addRow("Тема:", subject_edit)

        desc_edit = QTextEdit()
        layout.addRow("Описание:", desc_edit)

        date_edit = QDateTimeEdit(QDateTime.currentDateTime())
        date_edit.setCalendarPopup(True)
        layout.addRow("Дата/время:", date_edit)

        result_edit = QLineEdit()
        layout.addRow("Результат:", result_edit)

        next_action_edit = QLineEdit()
        layout.addRow("След. действие:", next_action_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            with SessionLocal() as session:
                try:
                    self.interaction_service.create(
                        session, company_id=self.company_id,
                        interaction_type=type_combo.currentText(),
                        event_date=date_edit.dateTime().toPython(),
                        subject=subject_edit.text(),
                        description=desc_edit.toPlainText() or None,
                        result=result_edit.text() or None,
                        next_action=next_action_edit.text() or None,
                    )
                    session.commit()
                    self.load_company(self.company_id)
                except Exception as e:
                    show_error_message(self, "Ошибка", str(e))

    def _show_interaction_detail(self, item: QListWidgetItem):
        interaction_id = item.data(Qt.UserRole)
        if not interaction_id: return
        QMessageBox.information(self, "Просмотр", f"Детали взаимодействия id={interaction_id} (заглушка)")

    # --------------------------------------------------------------
    # Tasks
    # --------------------------------------------------------------
    def _add_task_dialog(self):
        if not self.company_id: return
        dialog = QDialog(self)
        dialog.setWindowTitle("Новая задача")
        layout = QFormLayout(dialog)

        title_edit = QLineEdit()
        layout.addRow("Заголовок:", title_edit)

        desc_edit = QTextEdit()
        layout.addRow("Описание:", desc_edit)

        due_date_edit = QDateTimeEdit(QDateTime.currentDateTime())
        due_date_edit.setCalendarPopup(True)
        due_date_edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        layout.addRow("Срок:", due_date_edit)

        all_day_check = QCheckBox("Весь день (без времени)")
        all_day_check.stateChanged.connect(
            lambda state: due_date_edit.setDisplayFormat("dd.MM.yyyy" if state else "dd.MM.yyyy HH:mm"))
        layout.addRow(all_day_check)

        priority_combo = QComboBox()
        priority_combo.addItems(["low", "medium", "high"])
        layout.addRow("Приоритет:", priority_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            due_dt = due_date_edit.dateTime().toPython()
            if all_day_check.isChecked():
                due_dt = due_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            with SessionLocal() as session:
                try:
                    self.task_service.create(
                        session, company_id=self.company_id,
                        title=title_edit.text(),
                        description=desc_edit.toPlainText() or None,
                        due_date=due_dt,
                        priority=priority_combo.currentText(),
                    )
                    session.commit()
                    self.load_company(self.company_id)
                except Exception as e:
                    show_error_message(self, "Ошибка", str(e))

    def _toggle_task_status(self, item: QListWidgetItem):
        task_id = item.data(Qt.UserRole)
        if not task_id: return
        with SessionLocal() as session:
            try:
                task = self.task_service.repo.get(session, task_id)
                if task:
                    new_status = "open" if task.status == "done" else "done"
                    self.task_service.update_status(session, task_id, new_status)
                    session.commit()
                    self.load_company(self.company_id)
            except Exception as e:
                show_error_message(self, "Ошибка", str(e))

    # --------------------------------------------------------------
    # Documents
    # --------------------------------------------------------------
    def _add_document_dialog(self):
        if not self.company_id: return
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл")
        if not file_path: return
        original_name = os.path.basename(file_path)
        comment, ok = QInputDialog.getText(self, "Комментарий", "Введите краткое описание (необязательно):")
        if not ok: comment = ""
        with SessionLocal() as session:
            try:
                self.document_service.attach_to_entity(
                    session, source_path=file_path, original_name=original_name, doc_type="other",
                    entity_type="company", entity_id=self.company_id,
                    comment=comment if comment.strip() else None,
                )
                session.commit()
                self.load_company(self.company_id)
            except Exception as e:
                show_error_message(self, "Ошибка", str(e))

    def _on_doc_single_click(self, item: QTreeWidgetItem, column: int):
        file_path = item.data(0, Qt.UserRole)
        if file_path:
            self.file_preview_requested.emit(file_path)

    def _on_doc_double_clicked(self, item: QTreeWidgetItem, column: int):
        if column == 1: self._edit_comment(item)
        else: self._open_document(item)

    def _open_document(self, item: QTreeWidgetItem):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            QMessageBox.warning(self, "Ошибка", "Файл не найден.")

    def _edit_comment(self, item: QTreeWidgetItem):
        doc_id = item.data(0, Qt.UserRole + 1)
        if not doc_id: return
        current_comment = item.text(1)
        new_comment, ok = QInputDialog.getText(self, "Комментарий", "Введите комментарий:", text=current_comment)
        if ok:
            with SessionLocal() as session:
                try:
                    self.document_service.update_comment(session, doc_id, new_comment)
                    session.commit()
                    item.setText(1, new_comment)
                except Exception as e:
                    show_error_message(self, "Ошибка", str(e))

    def _on_doc_context_menu(self, pos):
        item = self.docs_tree.itemAt(pos)
        if not item: return
        file_path = item.data(0, Qt.UserRole)
        doc_id = item.data(0, Qt.UserRole + 1)
        menu = QMenu(self)
        open_action = menu.addAction("Открыть")
        open_folder_action = menu.addAction("Показать в папке")
        edit_comment_action = menu.addAction("Изменить комментарий")
        delete_action = menu.addAction("Удалить")
        action = menu.exec(self.docs_tree.mapToGlobal(pos))
        if action == open_action: self._open_document(item)
        elif action == open_folder_action:
            folder = os.path.dirname(file_path)
            if os.path.exists(folder): QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        elif action == edit_comment_action: self._edit_comment(item)
        elif action == delete_action: self._delete_document(doc_id, file_path)

    def _delete_document(self, doc_id, file_path):
        msg = QMessageBox(self)
        msg.setWindowTitle("Удаление документа")
        msg.setText("Что вы хотите удалить?")
        btn_delete_record = msg.addButton("Только запись в БД", QMessageBox.AcceptRole)
        btn_delete_with_file = msg.addButton("Запись и файл на диске", QMessageBox.DestructiveRole)
        btn_cancel = msg.addButton("Отмена", QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_cancel: return
        delete_file = (msg.clickedButton() == btn_delete_with_file)
        with SessionLocal() as session:
            try:
                self.document_service.remove(session, doc_id, delete_file=delete_file)
                session.commit()
                self.load_company(self.company_id)
                self.file_preview_requested.emit("")
            except Exception as e:
                show_error_message(self, "Ошибка", f"Не удалось удалить документ:\n{e}")