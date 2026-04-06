"""Điểm vào ứng dụng quản lý quán Bi-a (PyQt6 + SQLite, MVC)."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from app.controllers import MainController
from app.database import Database
from app.views import MainWindowView


def main() -> int:
    app = QApplication(sys.argv)
    db = Database()
    db.init_schema()
    view = MainWindowView()
    ctrl = MainController(view, db)
    ctrl.setup()
    view.show()
    try:
        return app.exec()
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
