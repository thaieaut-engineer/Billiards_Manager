"""Model: nhân viên."""

from __future__ import annotations

import sqlite3


class NhanVienModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_all(self) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            """SELECT n.id, n.ten, n.so_dien_thoai,
                      n.luong_gio, n.luong,
                      COALESCE(cv.ten, n.chuc_vu, '') AS chuc_vu,
                      n.chuc_vu_id
               FROM nhan_vien n
               LEFT JOIN chuc_vu cv ON cv.id = n.chuc_vu_id
               ORDER BY n.id"""
        )
        return cur.fetchall()

    def get(self, nv_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            """SELECT n.id, n.ten, n.so_dien_thoai,
                      n.luong_gio, n.luong,
                      COALESCE(cv.ten, n.chuc_vu, '') AS chuc_vu,
                      n.chuc_vu_id
               FROM nhan_vien n
               LEFT JOIN chuc_vu cv ON cv.id = n.chuc_vu_id
               WHERE n.id = ?""",
            (nv_id,),
        )
        return cur.fetchone()

    def create(
        self,
        ten: str,
        so_dien_thoai: str | None,
        luong_gio: float | None,
        chuc_vu_id: int | None,
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO nhan_vien (ten, so_dien_thoai, luong_gio, chuc_vu_id) VALUES (?, ?, ?, ?)",
            (ten.strip(), so_dien_thoai or None, luong_gio, chuc_vu_id),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update(
        self,
        nv_id: int,
        ten: str,
        so_dien_thoai: str | None,
        luong_gio: float | None,
        chuc_vu_id: int | None,
    ) -> None:
        self._conn.execute(
            "UPDATE nhan_vien SET ten = ?, so_dien_thoai = ?, luong_gio = ?, chuc_vu_id = ? WHERE id = ?",
            (ten.strip(), so_dien_thoai or None, luong_gio, chuc_vu_id, nv_id),
        )
        self._conn.commit()

    def delete(self, nv_id: int) -> None:
        self._conn.execute("DELETE FROM nhan_vien WHERE id = ?", (nv_id,))
        self._conn.commit()
