"""Hộp thoại đăng ký / tạo tài khoản."""

from __future__ import annotations

import sqlite3

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.models.tai_khoan_model import TaiKhoanModel


class RegisterDialog(QDialog):
    def __init__(
        self,
        model: TaiKhoanModel,
        *,
        first_user: bool = False,
        allow_role_select: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._first_user = first_user
        self._allow_role = allow_role_select

        if first_user:
            self.setWindowTitle("Đăng ký — tài khoản quản trị đầu tiên")
        else:
            self.setWindowTitle("Tạo tài khoản")

        self._edit_user = QLineEdit()
        self._edit_ho_ten = QLineEdit()
        self._edit_pw = QLineEdit()
        self._edit_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._edit_pw2 = QLineEdit()
        self._edit_pw2.setEchoMode(QLineEdit.EchoMode.Password)

        self._combo_role = QComboBox()
        self._combo_role.addItem("Quản trị viên", "admin")
        self._combo_role.addItem("Nhân viên", "nhan_vien")

        form = QFormLayout()
        form.addRow("Tên đăng nhập", self._edit_user)
        form.addRow("Họ tên", self._edit_ho_ten)
        form.addRow("Mật khẩu", self._edit_pw)
        form.addRow("Nhập lại mật khẩu", self._edit_pw2)
        if allow_role_select and not first_user:
            form.addRow("Vai trò", self._combo_role)
        elif first_user:
            form.addRow("", QLabel("Tài khoản đầu sẽ là quản trị viên."))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._try_save)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(buttons)

        if first_user:
            self._combo_role.setCurrentIndex(0)

    def _try_save(self) -> None:
        user = self._edit_user.text().strip()
        ho_ten = self._edit_ho_ten.text().strip()
        pw = self._edit_pw.text()
        pw2 = self._edit_pw2.text()
        if len(user) < 2:
            QMessageBox.warning(self, "Thiếu dữ liệu", "Tên đăng nhập ít nhất 2 ký tự.")
            return
        if len(pw) < 4:
            QMessageBox.warning(self, "Mật khẩu", "Mật khẩu ít nhất 4 ký tự.")
            return
        if pw != pw2:
            QMessageBox.warning(self, "Mật khẩu", "Hai lần nhập mật khẩu không khớp.")
            return
        if self._first_user:
            role = "admin"
        elif self._allow_role:
            role = self._combo_role.currentData()
        else:
            role = "nhan_vien"
        try:
            self._model.create(user, pw, ho_ten, role)
        except (ValueError, sqlite3.Error) as e:
            QMessageBox.critical(self, "Lỗi", str(e))
            return
        self.accept()
