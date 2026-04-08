"""Model: chức vụ (hệ số lương)."""

from __future__ import annotations

import sqlite3
from datetime import datetime


class ChucVuModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_all(self) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            "SELECT id, ten, he_so, ngay_tao FROM chuc_vu ORDER BY id"
        )
        return cur.fetchall()

    def get(self, cv_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT id, ten, he_so, ngay_tao FROM chuc_vu WHERE id = ?",
            (cv_id,),
        )
        return cur.fetchone()

    def create(self, ten: str, he_so: float) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self._conn.execute(
            "INSERT INTO chuc_vu (ten, he_so, ngay_tao) VALUES (?, ?, ?)",
            (ten.strip(), float(he_so), now),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update(self, cv_id: int, ten: str, he_so: float) -> None:
        self._conn.execute(
            "UPDATE chuc_vu SET ten = ?, he_so = ? WHERE id = ?",
            (ten.strip(), float(he_so), cv_id),
        )
        self._conn.commit()

    def delete(self, cv_id: int) -> None:
        self._conn.execute("DELETE FROM chuc_vu WHERE id = ?", (cv_id,))
        self._conn.commit()

