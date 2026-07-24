# -*- coding: utf-8 -*-
"""
Пакет sales_assistant.ui.main_window.

Главное окно приложения.
"""
from PySide6.QtWidgets import QMainWindow, QDockWidget, QLabel
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sales Assistant")
        self.resize(1200, 800)
        self._setup_dock_panels()

    def _setup_dock_panels(self):
        # Навигационная панель
        nav_dock = QDockWidget("Навигация", self)
        nav_dock.setWidget(QLabel("Панель навигации"))
        nav_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, nav_dock)

        # Панель задач (дашборд) — пока пустая
        dashboard_dock = QDockWidget("Дашборд", self)
        dashboard_dock.setWidget(QLabel("Сводка"))
        self.addDockWidget(Qt.RightDockWidgetArea, dashboard_dock)