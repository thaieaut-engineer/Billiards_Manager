"""Hộp thoại đăng ký / tạo tài khoản."""

from __future__ import annotations

import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
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
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._model = model
        self._first_user = first_user
        self._allow_role = allow_role_select

        if first_user:
            self.setWindowTitle("Đăng ký — tài khoản quản trị đầu tiên")
        else:
            self.setWindowTitle("Tạo tài khoản")

        title = QLabel("Tạo tài khoản")
        title.setObjectName("dlgTitle")
        subtitle_text = (
            "Tạo tài khoản quản trị đầu tiên."
            if first_user
            else "Nhập thông tin tài khoản mới."
        )
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("dlgSubtitle")
        subtitle.setWordWrap(True)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)

        self._edit_user = QLineEdit()
        self._edit_user.setPlaceholderText("vd: admin, nv01...")
        self._edit_user.setMinimumWidth(280)
        self._edit_ho_ten = QLineEdit()
        self._edit_ho_ten.setPlaceholderText("vd: Nguyễn Văn A")
        self._edit_pw = QLineEdit()
        self._edit_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._edit_pw.setPlaceholderText("Mật khẩu")
        self._edit_pw2 = QLineEdit()
        self._edit_pw2.setEchoMode(QLineEdit.EchoMode.Password)
        self._edit_pw2.setPlaceholderText("Nhập lại mật khẩu")
        self._edit_pw2.returnPressed.connect(self._try_save)

        self._combo_role = QComboBox()
        self._combo_role.addItem("Quản trị viên", "admin")
        self._combo_role.addItem("Nhân viên", "nhan_vien")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        form.addRow("Tên đăng nhập", self._edit_user)
        form.addRow("Họ tên", self._edit_ho_ten)
        form.addRow("Mật khẩu", self._edit_pw)
        form.addRow("Nhập lại mật khẩu", self._edit_pw2)
        if allow_role_select and not first_user:
            form.addRow("Vai trò", self._combo_role)
        elif first_user:
            form.addRow("", QLabel("Tài khoản đầu sẽ là quản trị viên."))

        self._chk_show_pw = QCheckBox("Hiện mật khẩu")
        self._chk_show_pw.toggled.connect(self._toggle_password_visible)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Đăng ký" if first_user else "Tạo"
        )
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy")
        buttons.accepted.connect(self._try_save)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 14)
        lay.setSpacing(12)
        lay.addWidget(title)
        lay.addWidget(subtitle)
        lay.addWidget(sep)
        lay.addLayout(form)
        lay.addWidget(self._chk_show_pw)
        lay.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog { background: #ffffff; }
            QLabel#dlgTitle { font-size: 18px; font-weight: 700; color: #0f172a; }
            QLabel#dlgSubtitle { color: #475569; }
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            QLineEdit:focus { border: 1px solid #3b82f6; }
            QComboBox {
                padding: 7px 10px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            QComboBox:focus { border: 1px solid #3b82f6; }
            QPushButton {
                padding: 8px 12px;
                border-radius: 8px;
            }
            QPushButton:hover { background: #f1f5f9; }
            QDialogButtonBox QPushButton { min-width: 96px; }
            """
        )

        if first_user:
            self._combo_role.setCurrentIndex(0)

    def _toggle_password_visible(self, checked: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self._edit_pw.setEchoMode(mode)
        self._edit_pw2.setEchoMode(mode)

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
