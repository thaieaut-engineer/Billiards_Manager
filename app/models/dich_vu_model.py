"""Model: dịch vụ (đồ uống, đồ ăn)."""

from __future__ import annotations

import sqlite3


class DichVuModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_all(self) -> list[sqlite3.Row]:
        cur = self._conn.execute("SELECT id, ten, gia FROM dich_vu ORDER BY id")
        return cur.fetchall()

    def get(self, dv_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT id, ten, gia FROM dich_vu WHERE id = ?", (dv_id,)
        )
        return cur.fetchone()

    def create(self, ten: str, gia: float) -> int:
        cur = self._conn.execute(
            "INSERT INTO dich_vu (ten, gia) VALUES (?, ?)",
            (ten.strip(), float(gia)),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update(self, dv_id: int, ten: str, gia: float) -> None:
        self._conn.execute(
            "UPDATE dich_vu SET ten = ?, gia = ? WHERE id = ?",
            (ten.strip(), float(gia), dv_id),
        )
        self._conn.commit()

    def delete(self, dv_id: int) -> None:
        self._conn.execute("DELETE FROM dich_vu WHERE id = ?", (dv_id,))
        self._conn.commit()
