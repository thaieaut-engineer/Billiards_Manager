"""Đổi mật khẩu tài khoản (dùng khi quản trị đặt lại mật khẩu)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class ChangePasswordDialog(QDialog):
    def __init__(self, ten_dang_nhap: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Đổi mật khẩu")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._pw = QLineEdit()
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw2 = QLineEdit()
        self._pw2.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Mật khẩu mới", self._pw)
        form.addRow("Nhập lại", self._pw2)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_ok)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"Tài khoản: {ten_dang_nhap}"))
        lay.addLayout(form)
        lay.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog { background: #ffffff; }
            QLineEdit { padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px; }
            QLineEdit:focus { border: 1px solid #3b82f6; }
            """
        )

    def _accept_if_ok(self) -> None:
        a = self._pw.text()
        b = self._pw2.text()
        if len(a) < 4:
            QMessageBox.warning(self, "Mật khẩu", "Mật khẩu ít nhất 4 ký tự.")
            return
        if a != b:
            QMessageBox.warning(self, "Mật khẩu", "Hai lần nhập không khớp.")
            return
        self.accept()

    def password(self) -> str:
        return self._pw.text()
