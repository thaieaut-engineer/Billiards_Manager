"""Model: nhân viên."""

from __future__ import annotations

import sqlite3


class NhanVienModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_all(self) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            "SELECT id, ten, so_dien_thoai, luong, chuc_vu FROM nhan_vien ORDER BY id"
        )
        return cur.fetchall()

    def get(self, nv_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT id, ten, so_dien_thoai, luong, chuc_vu FROM nhan_vien WHERE id = ?",
            (nv_id,),
        )
        return cur.fetchone()

    def create(
        self, ten: str, so_dien_thoai: str | None, luong: float | None, chuc_vu: str | None
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO nhan_vien (ten, so_dien_thoai, luong, chuc_vu) VALUES (?, ?, ?, ?)",
            (ten.strip(), so_dien_thoai or None, luong, chuc_vu or None),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update(
        self,
        nv_id: int,
        ten: str,
        so_dien_thoai: str | None,
        luong: float | None,
        chuc_vu: str | None,
    ) -> None:
        self._conn.execute(
            "UPDATE nhan_vien SET ten = ?, so_dien_thoai = ?, luong = ?, chuc_vu = ? WHERE id = ?",
            (ten.strip(), so_dien_thoai or None, luong, chuc_vu or None, nv_id),
        )
        self._conn.commit()

    def delete(self, nv_id: int) -> None:
        self._conn.execute("DELETE FROM nhan_vien WHERE id = ?", (nv_id,))
        self._conn.commit()
