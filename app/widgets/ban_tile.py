"""Ô bàn hình chữ nhật (sơ đồ quán)."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class BanTile(QFrame):
    clicked = pyqtSignal(int)

    def __init__(
        self,
        ban_id: int,
        ten_ban: str,
        trong: bool,
        gia_gio_str: str,
        loai_ban: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.ban_id = ban_id
        self._trong = trong
        self._selected = False

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(168, 100)
        self.setMaximumHeight(128)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        lay = QVBoxLayout(self)
        lay.setSpacing(4)
        name = QLabel(ten_ban)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("font-weight: bold; font-size: 13pt; background: transparent;")
        st = QLabel("Trống" if trong else "Đang chơi")
        st.setAlignment(Qt.AlignmentFlag.AlignCenter)
        st.setStyleSheet("font-size: 10pt; background: transparent;")
        gia = QLabel(f"{gia_gio_str} đ/giờ")
        gia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gia.setStyleSheet("font-size: 9pt; color: #424242; background: transparent;")
        lay.addWidget(name)
        loai_t = (loai_ban or "").strip()
        if loai_t:
            lo = QLabel(loai_t)
            lo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lo.setStyleSheet("font-size: 10pt; color: #37474f; background: transparent;")
            lay.addWidget(lo)
        lay.addWidget(st)
        lay.addWidget(gia)

        self._apply_style()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_style()

    def _apply_style(self) -> None:
        base = "#c8e6c9" if self._trong else "#ffccbc"
        if self._selected:
            border = "#1565c0"
            width = 3
        else:
            border = "#2e7d32" if self._trong else "#e64a19"
            width = 2
        self.setStyleSheet(
            f"QFrame {{ background-color: {base}; border: {width}px solid {border}; "
            f"border-radius: 8px; }}"
        )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.ban_id)
        super().mousePressEvent(event)
