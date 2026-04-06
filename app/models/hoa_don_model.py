"""Model: hóa đơn và chi tiết."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChiTietLine:
    dich_vu_id: int
    so_luong: int
    thanh_tien: float


class HoaDonModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create_with_details(
        self,
        phien_id: int,
        thoi_gian_choi_gio: float,
        tien_ban: float,
        tien_dich_vu: float,
        tong_tien: float,
        chi_tiet: list[ChiTietLine],
    ) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self._conn.execute(
            """INSERT INTO hoa_don (phien_id, thoi_gian_choi, tien_ban, tien_dich_vu, tong_tien, ngay_tao)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                phien_id,
                thoi_gian_choi_gio,
                tien_ban,
                tien_dich_vu,
                tong_tien,
                now,
            ),
        )
        hd_id = int(cur.lastrowid)
        for line in chi_tiet:
            self._conn.execute(
                """INSERT INTO chi_tiet_hoa_don (hoa_don_id, dich_vu_id, so_luong, thanh_tien)
                   VALUES (?, ?, ?, ?)""",
                (hd_id, line.dich_vu_id, line.so_luong, line.thanh_tien),
            )
        self._conn.commit()
        return hd_id

    def list_all(self, limit: int = 500) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            """SELECT h.id, h.phien_id, h.thoi_gian_choi, h.tien_ban, h.tien_dich_vu,
                      h.tong_tien, h.ngay_tao, b.ten_ban
               FROM hoa_don h
               JOIN phien_choi p ON p.id = h.phien_id
               JOIN ban b ON b.id = p.ban_id
               ORDER BY h.id DESC
               LIMIT ?""",
            (limit,),
        )
        return cur.fetchall()

    def list_by_date_range(self, tu_ngay: str, den_ngay: str) -> list[sqlite3.Row]:
        """tu_ngay, den_ngay: 'YYYY-MM-DD' — so sánh theo phần ngày của ngay_tao."""
        cur = self._conn.execute(
            """SELECT h.id, h.phien_id, h.thoi_gian_choi, h.tien_ban, h.tien_dich_vu,
                      h.tong_tien, h.ngay_tao, b.ten_ban
               FROM hoa_don h
               JOIN phien_choi p ON p.id = h.phien_id
               JOIN ban b ON b.id = p.ban_id
               WHERE date(h.ngay_tao) >= date(?) AND date(h.ngay_tao) <= date(?)
               ORDER BY h.id DESC""",
            (tu_ngay, den_ngay),
        )
        return cur.fetchall()

    def get_full(self, hoa_don_id: int) -> tuple[sqlite3.Row | None, list[sqlite3.Row]]:
        cur = self._conn.execute(
            """SELECT h.*, b.ten_ban, p.gio_bat_dau, p.gio_ket_thuc
               FROM hoa_don h
               JOIN phien_choi p ON p.id = h.phien_id
               JOIN ban b ON b.id = p.ban_id
               WHERE h.id = ?""",
            (hoa_don_id,),
        )
        head = cur.fetchone()
        if not head:
            return None, []
        cur2 = self._conn.execute(
            """SELECT c.dich_vu_id, c.so_luong, c.thanh_tien, d.ten AS ten_dv
               FROM chi_tiet_hoa_don c
               JOIN dich_vu d ON d.id = c.dich_vu_id
               WHERE c.hoa_don_id = ?
               ORDER BY c.id""",
            (hoa_don_id,),
        )
        return head, cur2.fetchall()

    def tong_doanh_thu_khoang(self, tu_ngay: str, den_ngay: str) -> float:
        cur = self._conn.execute(
            """SELECT COALESCE(SUM(tong_tien), 0) AS s
               FROM hoa_don
               WHERE date(ngay_tao) >= date(?) AND date(ngay_tao) <= date(?)""",
            (tu_ngay, den_ngay),
        )
        row = cur.fetchone()
        return float(row["s"] if row else 0.0)

    def finalize_session_checkout(
        self,
        phien_id: int,
        ban_id: int,
        thoi_gian_choi_gio: float,
        tien_ban: float,
        tien_dich_vu: float,
        tong_tien: float,
        chi_tiet: list[ChiTietLine],
    ) -> int:
        """Một giao dịch: kết thúc phiên, tạo hóa đơn, chi tiết, trả bàn về trống."""
        now = datetime.now().isoformat(timespec="seconds")
        conn = self._conn
        try:
            conn.execute("BEGIN")
            conn.execute(
                "UPDATE phien_choi SET gio_ket_thuc = ? WHERE id = ?",
                (now, phien_id),
            )
            cur = conn.execute(
                """INSERT INTO hoa_don (phien_id, thoi_gian_choi, tien_ban, tien_dich_vu, tong_tien, ngay_tao)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    phien_id,
                    thoi_gian_choi_gio,
                    tien_ban,
                    tien_dich_vu,
                    tong_tien,
                    now,
                ),
            )
            hd_id = int(cur.lastrowid)
            for line in chi_tiet:
                conn.execute(
                    """INSERT INTO chi_tiet_hoa_don (hoa_don_id, dich_vu_id, so_luong, thanh_tien)
                       VALUES (?, ?, ?, ?)""",
                    (hd_id, line.dich_vu_id, line.so_luong, line.thanh_tien),
                )
            conn.execute(
                "UPDATE ban SET trang_thai = 'trong' WHERE id = ?",
                (ban_id,),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return hd_id
