"""Ô bàn hình chữ nhật (sơ đồ quán)."""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class BanTile(QFrame):
    clicked = pyqtSignal(int)
    # Mặt bàn nằm ngang: rộng > cao (gần tỉ lệ bàn thật ~2:1).
    _ASPECT_H_PER_W = 0.52
    _MIN_W = 240

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
        self.setMinimumSize(self._MIN_W, int(self._MIN_W * self._ASPECT_H_PER_W))
        sp = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)

        lay = QVBoxLayout(self)
        lay.setSpacing(2)
        # Chừa khoảng cho thành + lỗ bàn.
        lay.setContentsMargins(18, 16, 18, 16)

        name = QLabel(ten_ban)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(
            "font-weight: 700; font-size: 14pt; color: #f8fafc; background: transparent;"
        )

        st = QLabel("TRỐNG" if trong else "ĐANG CHƠI")
        st.setAlignment(Qt.AlignmentFlag.AlignCenter)
        st.setStyleSheet("font-size: 9pt; font-weight: 700; letter-spacing: 1px; background: transparent;")
        gia = QLabel(f"{gia_gio_str} đ/giờ")
        gia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gia.setStyleSheet("font-size: 9pt; color: #e2e8f0; background: transparent;")
        lay.addWidget(name)
        loai_t = (loai_ban or "").strip()
        if loai_t:
            lo = QLabel(loai_t)
            lo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lo.setStyleSheet("font-size: 10pt; color: #cbd5e1; background: transparent;")
            lay.addWidget(lo)
        lay.addWidget(st)
        lay.addWidget(gia)

        # Để paintEvent tự vẽ nền; labels trong suốt.
        self.setStyleSheet("QFrame { background: transparent; border: none; }")

    def hasHeightForWidth(self) -> bool:  # Qt layout hint
        return True

    def heightForWidth(self, w: int) -> int:  # giữ tỉ lệ khi resize
        return max(int(w * self._ASPECT_H_PER_W), self.minimumHeight())

    def sizeHint(self) -> QSize:
        w = 300
        return QSize(w, self.heightForWidth(w))

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        r = self.rect().adjusted(2, 2, -2, -2)

        # Màu bàn: thành gỗ tối (ít "vệt"), mặt nỉ xanh.
        rail = QColor("#2b1a10")  # gỗ tối, gần như phẳng
        rail2 = QColor("#3a2416")
        felt = QColor("#0b6b3a") if self._trong else QColor("#0a4a2a")
        felt2 = QColor("#0a5f34") if self._trong else QColor("#083f24")

        # Viền highlight
        accent = QColor("#60a5fa") if self._selected else (QColor("#34d399") if self._trong else QColor("#fb923c"))

        outer_radius = 16
        inner_radius = 12
        rail_w = 10

        # Thành bàn (outer)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(rail2)
        p.drawRoundedRect(r, outer_radius, outer_radius)

        # Đường viền thành
        pen = QPen(rail)
        pen.setWidth(2)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, outer_radius, outer_radius)

        # Mặt nỉ (inner)
        inner = r.adjusted(rail_w, rail_w, -rail_w, -rail_w)
        p.setPen(Qt.PenStyle.NoPen)
        # gradient nhẹ cho mặt nỉ
        # (tạo bằng cách vẽ 2 lớp)
        p.setBrush(felt)
        p.drawRoundedRect(inner, inner_radius, inner_radius)
        p.setBrush(QColor(felt2.red(), felt2.green(), felt2.blue(), 120))
        p.drawRoundedRect(inner.adjusted(2, 2, -2, -2), inner_radius - 1, inner_radius - 1)

        # Lỗ bàn (6 lỗ): 4 góc + 2 giữa cạnh dài
        pocket = QColor("#050505")
        pocket_r = 8
        pockets = [
            inner.topLeft(),
            inner.topRight(),
            inner.bottomLeft(),
            inner.bottomRight(),
            inner.topLeft() + (inner.topRight() - inner.topLeft()) / 2,
            inner.bottomLeft() + (inner.bottomRight() - inner.bottomLeft()) / 2,
        ]
        p.setBrush(pocket)
        p.setPen(Qt.PenStyle.NoPen)
        for pt in pockets:
            p.drawEllipse(pt, pocket_r, pocket_r)

        # Kim cương (diamond sights) nhỏ trên thành
        diamond = QColor(240, 240, 240, 150)
        p.setBrush(diamond)
        for t in (0.25, 0.5, 0.75):
            x = int(r.left() + r.width() * t)
            y_top = int(r.top() + rail_w / 2)
            y_bot = int(r.bottom() - rail_w / 2)
            p.drawEllipse(x, y_top, 2, 2)
            p.drawEllipse(x, y_bot, 2, 2)

        # Outline khi chọn/hover (vòng ngoài)
        if self._selected or self.underMouse():
            pen = QPen(accent)
            pen.setWidth(3 if self._selected else 2)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), outer_radius, outer_radius)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.ban_id)
        super().mousePressEvent(event)
