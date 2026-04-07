"""Model: loại bàn (giá mặc định + sale)."""

from __future__ import annotations

import sqlite3
from datetime import datetime


class LoaiBanModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_all(self) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            """SELECT id, ten, gia_gio_mac_dinh, sale_percent, ngay_tao
               FROM loai_ban
               ORDER BY ten COLLATE NOCASE"""
        )
        return cur.fetchall()

    def get(self, loai_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT id, ten, gia_gio_mac_dinh, sale_percent, ngay_tao FROM loai_ban WHERE id = ?",
            (int(loai_id),),
        )
        return cur.fetchone()

    def get_by_name(self, ten: str) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT id, ten, gia_gio_mac_dinh, sale_percent, ngay_tao FROM loai_ban WHERE LOWER(ten) = LOWER(?)",
            (ten.strip(),),
        )
        return cur.fetchone()

    def create(self, ten: str, gia_gio_mac_dinh: float, sale_percent: float = 0.0) -> int:
        t = ten.strip()
        if not t:
            raise ValueError("Tên loại bàn không được trống.")
        sp = float(sale_percent)
        if sp < 0 or sp > 100:
            raise ValueError("Sale% phải trong khoảng 0..100.")
        now = datetime.now().isoformat(timespec="seconds")
        cur = self._conn.execute(
            """INSERT INTO loai_ban (ten, gia_gio_mac_dinh, sale_percent, ngay_tao)
               VALUES (?, ?, ?, ?)""",
            (t, float(gia_gio_mac_dinh), sp, now),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update(self, loai_id: int, ten: str, gia_gio_mac_dinh: float, sale_percent: float = 0.0) -> None:
        t = ten.strip()
        if not t:
            raise ValueError("Tên loại bàn không được trống.")
        sp = float(sale_percent)
        if sp < 0 or sp > 100:
            raise ValueError("Sale% phải trong khoảng 0..100.")
        self._conn.execute(
            "UPDATE loai_ban SET ten = ?, gia_gio_mac_dinh = ?, sale_percent = ? WHERE id = ?",
            (t, float(gia_gio_mac_dinh), sp, int(loai_id)),
        )
        self._conn.commit()

    def is_used(self, loai_id: int) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM ban WHERE loai_ban_id = ? LIMIT 1",
            (int(loai_id),),
        )
        return cur.fetchone() is not None

    def delete(self, loai_id: int) -> None:
        if self.is_used(loai_id):
            raise ValueError("Không thể xóa: loại bàn đang được sử dụng.")
        self._conn.execute("DELETE FROM loai_ban WHERE id = ?", (int(loai_id),))
        self._conn.commit()

