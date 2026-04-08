"""Model: ca làm (hệ số ca, ca đêm cao hơn)."""

from __future__ import annotations

import sqlite3
from datetime import datetime


class CaLamModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_all(self) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            "SELECT id, ten, gio_bat_dau, gio_ket_thuc, he_so, ngay_tao FROM ca_lam ORDER BY id"
        )
        return cur.fetchall()

    def get(self, ca_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT id, ten, gio_bat_dau, gio_ket_thuc, he_so, ngay_tao FROM ca_lam WHERE id = ?",
            (ca_id,),
        )
        return cur.fetchone()

    def create(self, ten: str, gio_bat_dau: str, gio_ket_thuc: str, he_so: float) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self._conn.execute(
            "INSERT INTO ca_lam (ten, gio_bat_dau, gio_ket_thuc, he_so, ngay_tao) VALUES (?, ?, ?, ?, ?)",
            (ten.strip(), gio_bat_dau.strip(), gio_ket_thuc.strip(), float(he_so), now),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update(self, ca_id: int, ten: str, gio_bat_dau: str, gio_ket_thuc: str, he_so: float) -> None:
        self._conn.execute(
            "UPDATE ca_lam SET ten = ?, gio_bat_dau = ?, gio_ket_thuc = ?, he_so = ? WHERE id = ?",
            (ten.strip(), gio_bat_dau.strip(), gio_ket_thuc.strip(), float(he_so), ca_id),
        )
        self._conn.commit()

    def delete(self, ca_id: int) -> None:
        self._conn.execute("DELETE FROM ca_lam WHERE id = ?", (ca_id,))
        self._conn.commit()

