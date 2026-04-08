"""Model: phân công ca (tích ca nào thì tính theo ca; tăng ca = thêm nhiều dòng)."""

from __future__ import annotations

import sqlite3
from datetime import datetime


class PhanCongModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(self, nhan_vien_id: int, ca_id: int, ngay: str, ghi_chu: str | None = None) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self._conn.execute(
            """INSERT INTO phan_cong_ca (nhan_vien_id, ca_id, ngay, ghi_chu, ngay_tao)
               VALUES (?, ?, ?, ?, ?)""",
            (nhan_vien_id, ca_id, ngay, (ghi_chu or "").strip() or None, now),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def delete(self, phan_cong_id: int) -> None:
        self._conn.execute("DELETE FROM phan_cong_ca WHERE id = ?", (phan_cong_id,))
        self._conn.commit()

    def list_by_date_range(self, tu_ngay: str, den_ngay: str) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            """SELECT pc.id, pc.ngay, pc.ghi_chu,
                      n.id AS nhan_vien_id, n.ten AS nhan_vien_ten,
                      COALESCE(cv.ten, n.chuc_vu, '') AS chuc_vu_ten,
                      n.luong_gio,
                      ca.id AS ca_id, ca.ten AS ca_ten, ca.gio_bat_dau, ca.gio_ket_thuc, ca.he_so AS ca_he_so,
                      COALESCE(cv.he_so, 1.0) AS cv_he_so
               FROM phan_cong_ca pc
               JOIN nhan_vien n ON n.id = pc.nhan_vien_id
               JOIN ca_lam ca ON ca.id = pc.ca_id
               LEFT JOIN chuc_vu cv ON cv.id = n.chuc_vu_id
               WHERE date(pc.ngay) >= date(?) AND date(pc.ngay) <= date(?)
               ORDER BY pc.ngay DESC, pc.id DESC""",
            (tu_ngay, den_ngay),
        )
        return cur.fetchall()

