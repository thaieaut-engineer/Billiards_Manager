"""View: cửa sổ chính — nạp file .ui từ Qt Designer."""

from __future__ import annotations

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow


class MainWindowView(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        ui_path = Path(__file__).resolve().parent.parent / "ui" / "main_window.ui"
        uic.loadUi(str(ui_path), self)
