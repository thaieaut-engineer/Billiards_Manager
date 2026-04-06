"""Điểm vào ứng dụng quản lý quán Bi-a (PyQt6 + SQLite, MVC)."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QDialog

from app.controllers import MainController
from app.database import Database
from app.dialogs import LoginDialog
from app.views import MainWindowView


def main() -> int:
    app = QApplication(sys.argv)
    db = Database()
    db.init_schema()

    def start_session(session) -> None:
        view = MainWindowView()
        ctrl = MainController(view, db, session)

        def on_logout() -> None:
            view.close()
            dlg = LoginDialog(db)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                app.quit()
                return
            start_session(dlg.session)

        ctrl.set_logout_handler(on_logout)
        ctrl.setup()
        view.show()

    dlg = LoginDialog(db)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        db.close()
        return 0
    start_session(dlg.session)
    try:
        return app.exec()
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
