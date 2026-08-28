# -*- coding: utf-8 -*-
"""
Вспомогательные диалоги (ошибки с копированием).
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QApplication
)

class ErrorDialog(QDialog):
    def __init__(self, title: str, message: str, details: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 300)

        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        full_text = message
        if details:
            full_text += "\n\n" + details
        self.text_edit.setPlainText(full_text)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        btn_copy = QPushButton("Копировать")
        btn_copy.clicked.connect(self._copy)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_copy)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _copy(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())


def show_error_message(parent, title: str, message: str, details: str = ""):
    dlg = ErrorDialog(title, message, details, parent)
    dlg.exec()