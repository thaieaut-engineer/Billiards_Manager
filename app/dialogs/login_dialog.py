"""Hộp thoại đăng nhập."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.auth import Session
from app.database import Database
from app.models.tai_khoan_model import TaiKhoanModel

from .register_dialog import RegisterDialog


class LoginDialog(QDialog):
    def __init__(self, database: Database, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Đăng nhập — Quản lý quán Bi-a")
        self._db = database
        self._conn = database.connect()
        self._model = TaiKhoanModel(self._conn)
        self.session: Session | None = None

        self._edit_user = QLineEdit()
        self._edit_user.setPlaceholderText("Tên đăng nhập")
        self._edit_pw = QLineEdit()
        self._edit_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._edit_pw.setPlaceholderText("Mật khẩu")

        form = QFormLayout()
        form.addRow("Tài khoản", self._edit_user)
        form.addRow("Mật khẩu", self._edit_pw)

        btn_row = QHBoxLayout()
        self._btn_register = QPushButton("Đăng ký tài khoản")
        self._btn_register.setToolTip(
            "Lần đầu: tạo tài khoản quản trị. Đã có tài khoản: xem hướng dẫn tạo thêm."
        )
        self._btn_register.clicked.connect(self._open_register)
        btn_row.addWidget(self._btn_register)
        btn_row.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Đăng nhập")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Thoát")
        buttons.accepted.connect(self._try_login)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Vui lòng đăng nhập để tiếp tục."))
        lay.addLayout(form)
        lay.addLayout(btn_row)
        lay.addWidget(buttons)

    def _open_register(self) -> None:
        if self._model.count() > 0:
            QMessageBox.information(
                self,
                "Đăng ký tài khoản",
                "Chỉ quản trị viên mới có thể tạo thêm tài khoản.\n\n"
                "Đăng nhập bằng tài khoản quản trị, sau đó chọn "
                "<b>Tài khoản → Tạo tài khoản...</b> trên cửa sổ chính.",
            )
            return
        dlg = RegisterDialog(self._model, first_user=True, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "Đã tạo tài khoản",
                "Đã đăng ký quản trị viên. Vui lòng đăng nhập.",
            )

    def _try_login(self) -> None:
        user = self._edit_user.text().strip()
        pw = self._edit_pw.text()
        if not user or not pw:
            QMessageBox.warning(self, "Thiếu dữ liệu", "Nhập tên đăng nhập và mật khẩu.")
            return
        sess = self._model.verify_login(user, pw)
        if sess is None:
            QMessageBox.warning(self, "Đăng nhập thất bại", "Sai tên đăng nhập hoặc mật khẩu.")
            return
        self.session = sess
        self.accept()
