"""Model: dịch vụ (mặt hàng)."""

from __future__ import annotations

import sqlite3


class DichVuModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_all(self, danh_muc_id: int | None = None) -> list[sqlite3.Row]:
        if danh_muc_id is None:
            cur = self._conn.execute(
                """SELECT d.id, d.ten, d.gia, d.danh_muc_id, m.ten AS danh_muc
                   FROM dich_vu d
                   JOIN danh_muc_dich_vu m ON m.id = d.danh_muc_id
                   ORDER BY m.ten COLLATE NOCASE, d.id"""
            )
        else:
            cur = self._conn.execute(
                """SELECT d.id, d.ten, d.gia, d.danh_muc_id, m.ten AS danh_muc
                   FROM dich_vu d
                   JOIN danh_muc_dich_vu m ON m.id = d.danh_muc_id
                   WHERE d.danh_muc_id = ?
                   ORDER BY d.id""",
                (int(danh_muc_id),),
            )
        return cur.fetchall()

    def get(self, dv_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            """SELECT d.id, d.ten, d.gia, d.danh_muc_id, m.ten AS danh_muc
               FROM dich_vu d
               JOIN danh_muc_dich_vu m ON m.id = d.danh_muc_id
               WHERE d.id = ?""",
            (dv_id,),
        )
        return cur.fetchone()

    def create(self, ten: str, gia: float, danh_muc_id: int) -> int:
        cur = self._conn.execute(
            "INSERT INTO dich_vu (ten, gia, danh_muc_id) VALUES (?, ?, ?)",
            (ten.strip(), float(gia), int(danh_muc_id)),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update(self, dv_id: int, ten: str, gia: float, danh_muc_id: int) -> None:
        self._conn.execute(
            "UPDATE dich_vu SET ten = ?, gia = ?, danh_muc_id = ? WHERE id = ?",
            (ten.strip(), float(gia), int(danh_muc_id), dv_id),
        )
        self._conn.commit()

    def delete(self, dv_id: int) -> None:
        self._conn.execute("DELETE FROM dich_vu WHERE id = ?", (dv_id,))
        self._conn.commit()
