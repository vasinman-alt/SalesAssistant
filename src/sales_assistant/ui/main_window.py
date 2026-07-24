# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.ui.main_window.

Главное окно приложения.
"""
import uuid
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QStackedWidget, QWidget, QVBoxLayout,
    QLabel, QMessageBox, QPushButton, QLineEdit, QFormLayout, QDialog,
    QDialogButtonBox
)
from PySide6.QtCore import Qt

from sales_assistant.db.engine import SessionLocal
from sales_assistant.services.user_service import UserService
from sales_assistant.services.company_service import CompanyService
from sales_assistant.ui.panels.navigation_panel import NavigationPanel
from sales_assistant.ui.panels.company_card import CompanyCardWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sales Assistant")
        self.resize(1200, 800)

        # Получаем или создаём локального пользователя
        self.current_user = UserService.ensure_local_admin()
        self.current_user_id = self.current_user.id

        self._setup_ui()

    def _setup_ui(self):
        # Центральный виджет с переключением представлений
        self.central_stack = QStackedWidget()

        # 0: приветственный экран
        welcome_widget = QLabel("Выберите компанию из списка или добавьте новую")
        welcome_widget.setAlignment(Qt.AlignCenter)
        self.central_stack.addWidget(welcome_widget)

        # 1: карточка компании
        self.company_card = CompanyCardWidget(self.current_user_id)
        self.central_stack.addWidget(self.company_card)

        self.setCentralWidget(self.central_stack)

        # Левая док-панель: навигация
        nav_panel = NavigationPanel(self.current_user_id)
        nav_panel.company_selected.connect(self._show_company)
        nav_panel.add_company_requested.connect(self._add_company_dialog)

        nav_dock = QDockWidget("Навигация", self)
        nav_dock.setObjectName("NavigationDock")  # <-- фикс: имя для поиска
        nav_dock.setWidget(nav_panel)
        nav_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, nav_dock)

    def _show_company(self, company_id: uuid.UUID):
        """Отобразить карточку выбранной компании."""
        self.company_card.load_company(company_id)
        self.central_stack.setCurrentIndex(1)

    def _add_company_dialog(self):
        """Диалог быстрого создания компании."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Новая компания")
        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        layout.addRow("Название:", name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            name = name_edit.text().strip()
            if name:
                with SessionLocal() as session:
                    try:
                        service = CompanyService(self.current_user_id)
                        company = service.create(session, name)
                        session.commit()
                        # Обновим список в панели навигации
                        nav_dock = self.findChild(QDockWidget, "NavigationDock")
                        if nav_dock:
                            nav_panel = nav_dock.widget()
                            nav_panel._load_companies()
                        self._show_company(company.id)
                    except Exception as e:
                        QMessageBox.critical(self, "Ошибка", f"Не удалось создать компанию:\n{e}")
                    finally:
                        session.close()
            else:
                QMessageBox.warning(self, "Предупреждение", "Название компании не может быть пустым.")