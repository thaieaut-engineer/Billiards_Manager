"""Model: bàn bi-a."""

from __future__ import annotations

import sqlite3


class BanModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_all(self, loc_loai: str | None = None) -> list[sqlite3.Row]:
        """loc_loai: None = tất cả; '' = chỉ bàn chưa gán loại; chuỗi khác = khớp loại."""
        base = "SELECT id, ten_ban, loai_ban, trang_thai, gia_gio FROM ban "
        if loc_loai is None:
            cur = self._conn.execute(base + "ORDER BY id")
        elif loc_loai == "":
            cur = self._conn.execute(
                base + "WHERE TRIM(COALESCE(loai_ban, '')) = '' ORDER BY id"
            )
        else:
            cur = self._conn.execute(
                base + "WHERE TRIM(loai_ban) = ? ORDER BY id",
                (loc_loai.strip(),),
            )
        return cur.fetchall()

    def distinct_loai_ban(self) -> list[str]:
        cur = self._conn.execute(
            """SELECT DISTINCT TRIM(loai_ban) AS lo FROM ban
               WHERE TRIM(COALESCE(loai_ban, '')) != ''
               ORDER BY lo COLLATE NOCASE"""
        )
        return [row[0] for row in cur.fetchall()]

    def has_any_empty_loai(self) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM ban WHERE TRIM(COALESCE(loai_ban, '')) = '' LIMIT 1"
        )
        return cur.fetchone() is not None

    def get(self, ban_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT id, ten_ban, loai_ban, trang_thai, gia_gio FROM ban WHERE id = ?",
            (ban_id,),
        )
        return cur.fetchone()

    def create(self, ten_ban: str, gia_gio: float, loai_ban: str = "") -> int:
        cur = self._conn.execute(
            "INSERT INTO ban (ten_ban, trang_thai, gia_gio, loai_ban) VALUES (?, 'trong', ?, ?)",
            (ten_ban.strip(), float(gia_gio), loai_ban.strip()),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update(self, ban_id: int, ten_ban: str, gia_gio: float, loai_ban: str = "") -> None:
        self._conn.execute(
            "UPDATE ban SET ten_ban = ?, gia_gio = ?, loai_ban = ? WHERE id = ?",
            (ten_ban.strip(), float(gia_gio), loai_ban.strip(), ban_id),
        )
        self._conn.commit()

    def delete(self, ban_id: int) -> None:
        self._conn.execute("DELETE FROM ban WHERE id = ?", (ban_id,))
        self._conn.commit()

    def set_trang_thai(self, ban_id: int, trang_thai: str) -> None:
        self._conn.execute(
            "UPDATE ban SET trang_thai = ? WHERE id = ?",
            (trang_thai, ban_id),
        )
        self._conn.commit()

    def list_trong(self) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            "SELECT id, ten_ban, loai_ban, trang_thai, gia_gio FROM ban WHERE trang_thai = 'trong' ORDER BY id"
        )
        return cur.fetchall()
