# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.ui.panels.company_card.

Виджет карточки компании с вкладками: общая информация, история, задачи, документы.
"""
import uuid
import os
import locale
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QGroupBox, QListWidget,
    QListWidgetItem, QTabWidget, QPushButton, QHBoxLayout, QMessageBox,
    QDialog, QLineEdit, QTextEdit, QComboBox, QDateTimeEdit, QDialogButtonBox,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu,
    QAbstractItemView, QCheckBox
)
from PySide6.QtCore import Qt, QDateTime, QUrl
from PySide6.QtGui import QDesktopServices

from sales_assistant.db.engine import SessionLocal
from sales_assistant.services.company_service import CompanyService
from sales_assistant.services.contact_service import ContactService
from sales_assistant.services.interaction_service import InteractionService
from sales_assistant.services.task_service import TaskService
from sales_assistant.services.document_service import DocumentService


class CompanyCardWidget(QWidget):
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

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        # ==================== Вкладка 1: Общая информация ====================
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)

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
        info_layout.addWidget(info_group)

        contacts_group = QGroupBox("Контакты")
        self.contacts_list = QListWidget()
        contacts_layout = QVBoxLayout()
        contacts_layout.addWidget(self.contacts_list)
        contacts_group.setLayout(contacts_layout)
        info_layout.addWidget(contacts_group)

        self.tabs.addTab(info_tab, "Общее")

        # ==================== Вкладка 2: История ====================
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        btn_add_interaction = QPushButton("+ Добавить взаимодействие")
        btn_add_interaction.clicked.connect(self._add_interaction_dialog)
        history_layout.addWidget(btn_add_interaction)
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._show_interaction_detail)
        history_layout.addWidget(self.history_list)
        self.tabs.addTab(history_tab, "История")

        # ==================== Вкладка 3: Задачи ====================
        tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(tasks_tab)
        btn_add_task = QPushButton("+ Добавить задачу")
        btn_add_task.clicked.connect(self._add_task_dialog)
        tasks_layout.addWidget(btn_add_task)
        self.tasks_list = QListWidget()
        self.tasks_list.itemDoubleClicked.connect(self._toggle_task_status)
        tasks_layout.addWidget(self.tasks_list)
        self.tabs.addTab(tasks_tab, "Задачи")

        # ==================== Вкладка 4: Документы ====================
        docs_tab = QWidget()
        docs_layout = QVBoxLayout(docs_tab)
        btn_add_doc = QPushButton("+ Добавить документ")
        btn_add_doc.clicked.connect(self._add_document_dialog)
        docs_layout.addWidget(btn_add_doc)

        self.docs_tree = QTreeWidget()
        self.docs_tree.setColumnCount(4)
        self.docs_tree.setHeaderLabels(["Имя файла", "Размер", "Дата создания", "Дата изменения"])
        self.docs_tree.setAlternatingRowColors(True)
        self.docs_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.docs_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.docs_tree.customContextMenuRequested.connect(self._on_doc_context_menu)
        self.docs_tree.itemDoubleClicked.connect(self._open_document)
        header = self.docs_tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 4):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        docs_layout.addWidget(self.docs_tree)
        self.tabs.addTab(docs_tab, "Документы")

        layout.addWidget(self.tabs)

    # --------------------------------------------------------------
    # Загрузка данных компании
    # --------------------------------------------------------------
    def load_company(self, company_id: uuid.UUID):
        self.company_id = company_id
        with SessionLocal() as session:
            try:
                company = self.company_service.get_by_id(session, company_id)
                if not company:
                    self._clear()
                    return

                # Основная информация
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

                # История
                interactions = self.interaction_service.get_by_company(session, company_id)
                self.history_list.clear()
                for i in interactions:
                    item_text = f"{i.event_date.strftime('%d.%m.%Y %H:%M')} - {i.subject} ({i.type})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, i.id)
                    self.history_list.addItem(item)

                # Задачи
                tasks = self.task_service.get_by_company(session, company_id)
                self.tasks_list.clear()
                for t in tasks:
                    due_str = f"до {t.due_date.strftime('%d.%m.%Y %H:%M')}" if t.due_date else "нет срока"
                    item_text = f"[{'✓' if t.status == 'done' else ' '}] {t.title} ({due_str})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, t.id)
                    self.tasks_list.addItem(item)

                # Документы
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

                    item = QTreeWidgetItem([
                        d.original_name,
                        size_str,
                        ctime_str,
                        mtime_str
                    ])
                    item.setData(0, Qt.UserRole, file_path)
                    if not exists:
                        item.setForeground(0, Qt.gray)
                        item.setToolTip(0, "Файл не найден по указанному пути")
                    self.docs_tree.addTopLevelItem(item)

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
        self.history_list.clear()
        self.tasks_list.clear()
        self.docs_tree.clear()

    # --------------------------------------------------------------
    # Диалоги добавления
    # --------------------------------------------------------------
    def _add_interaction_dialog(self):
        if not self.company_id:
            return
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
                        session,
                        company_id=self.company_id,
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
                    QMessageBox.critical(self, "Ошибка", str(e))

    def _show_interaction_detail(self, item: QListWidgetItem):
        interaction_id = item.data(Qt.UserRole)
        if not interaction_id:
            return
        # В будущем — полноценный диалог просмотра/редактирования
        QMessageBox.information(self, "Просмотр", f"Детали взаимодействия id={interaction_id} (заглушка)")

    def _add_task_dialog(self):
        if not self.company_id:
            return
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
            lambda state: due_date_edit.setDisplayFormat(
                "dd.MM.yyyy" if state else "dd.MM.yyyy HH:mm"
            )
        )
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
                        session,
                        company_id=self.company_id,
                        title=title_edit.text(),
                        description=desc_edit.toPlainText() or None,
                        due_date=due_dt,
                        priority=priority_combo.currentText(),
                    )
                    session.commit()
                    self.load_company(self.company_id)
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", str(e))

    def _toggle_task_status(self, item: QListWidgetItem):
        task_id = item.data(Qt.UserRole)
        if not task_id:
            return
        with SessionLocal() as session:
            try:
                task = self.task_service.repo.get(session, task_id)
                if task:
                    new_status = "open" if task.status == "done" else "done"
                    self.task_service.update_status(session, task_id, new_status)
                    session.commit()
                    self.load_company(self.company_id)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _add_document_dialog(self):
        if not self.company_id:
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл")
        if not file_path:
            return
        original_name = os.path.basename(file_path)
        with SessionLocal() as session:
            try:
                self.document_service.attach_to_entity(
                    session,
                    file_path=file_path,
                    original_name=original_name,
                    doc_type="other",
                    entity_type="company",
                    entity_id=self.company_id,
                )
                session.commit()
                self.load_company(self.company_id)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    # --------------------------------------------------------------
    # Работа с файлами документов
    # --------------------------------------------------------------
    def _open_document(self, item: QTreeWidgetItem):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            QMessageBox.warning(self, "Ошибка", "Файл не найден.")

    def _on_doc_context_menu(self, pos):
        item = self.docs_tree.itemAt(pos)
        if not item:
            return
        file_path = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        open_action = menu.addAction("Открыть")
        open_folder_action = menu.addAction("Показать в папке")
        action = menu.exec(self.docs_tree.mapToGlobal(pos))
        if action == open_action:
            self._open_document(item)
        elif action == open_folder_action:
            folder = os.path.dirname(file_path)
            if os.path.exists(folder):
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))