"""Model: phiên chơi."""

from __future__ import annotations

import sqlite3
from datetime import datetime


class PhienChoiModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(self, ban_id: int, nhan_vien_id: int | None) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self._conn.execute(
            """INSERT INTO phien_choi (ban_id, nhan_vien_id, gio_bat_dau, gio_ket_thuc)
               VALUES (?, ?, ?, NULL)""",
            (ban_id, nhan_vien_id, now),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def end_session(self, phien_id: int) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        self._conn.execute(
            "UPDATE phien_choi SET gio_ket_thuc = ? WHERE id = ?",
            (now, phien_id),
        )
        self._conn.commit()

    def list_active(self) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            """SELECT p.id, p.ban_id, p.nhan_vien_id, p.gio_bat_dau, b.ten_ban, b.gia_gio
               FROM phien_choi p
               JOIN ban b ON b.id = p.ban_id
               WHERE p.gio_ket_thuc IS NULL
               ORDER BY p.id"""
        )
        return cur.fetchall()

    def get(self, phien_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            """SELECT p.id, p.ban_id, p.nhan_vien_id, p.gio_bat_dau, p.gio_ket_thuc,
                      b.ten_ban, b.gia_gio
               FROM phien_choi p
               JOIN ban b ON b.id = p.ban_id
               WHERE p.id = ?""",
            (phien_id,),
        )
        return cur.fetchone()
