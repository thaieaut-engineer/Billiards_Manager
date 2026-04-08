"""Model: danh mục dịch vụ (nhóm đồ ăn, thức uống, ...)."""

from __future__ import annotations

import sqlite3
from datetime import datetime


class DanhMucDichVuModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_all(self) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            """SELECT id, ten, ngay_tao FROM danh_muc_dich_vu
               ORDER BY ten COLLATE NOCASE"""
        )
        return cur.fetchall()

    def get(self, dm_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT id, ten, ngay_tao FROM danh_muc_dich_vu WHERE id = ?",
            (int(dm_id),),
        )
        return cur.fetchone()

    def get_by_name(self, ten: str) -> sqlite3.Row | None:
        cur = self._conn.execute(
            """SELECT id, ten, ngay_tao FROM danh_muc_dich_vu
               WHERE LOWER(ten) = LOWER(?)""",
            (ten.strip(),),
        )
        return cur.fetchone()

    def create(self, ten: str) -> int:
        t = ten.strip()
        if not t:
            raise ValueError("Tên danh mục không được trống.")
        now = datetime.now().isoformat(timespec="seconds")
        cur = self._conn.execute(
            "INSERT INTO danh_muc_dich_vu (ten, ngay_tao) VALUES (?, ?)",
            (t, now),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update(self, dm_id: int, ten: str) -> None:
        t = ten.strip()
        if not t:
            raise ValueError("Tên danh mục không được trống.")
        self._conn.execute(
            "UPDATE danh_muc_dich_vu SET ten = ? WHERE id = ?",
            (t, int(dm_id)),
        )
        self._conn.commit()

    def is_used(self, dm_id: int) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM dich_vu WHERE danh_muc_id = ? LIMIT 1",
            (int(dm_id),),
        )
        return cur.fetchone() is not None

    def delete(self, dm_id: int) -> None:
        if self.is_used(dm_id):
            raise ValueError("Không thể xóa: danh mục đang có dịch vụ.")
        self._conn.execute("DELETE FROM danh_muc_dich_vu WHERE id = ?", (int(dm_id),))
        self._conn.commit()
