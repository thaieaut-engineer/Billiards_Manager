"""Model: chốt & trả lương theo kỳ (ngày 15 hằng tháng)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass
class BangLuongDong:
    nhan_vien_id: int
    ten: str
    chuc_vu: str
    luong_gio: float
    tong_gio: float
    tong_tien: float


def _parse_hhmm(s: str) -> tuple[int, int]:
    hh, mm = s.strip().split(":")
    return int(hh), int(mm)


def _hours_of_shift(ngay: str, gio_bat_dau: str, gio_ket_thuc: str) -> float:
    d = datetime.fromisoformat(ngay)
    h1, m1 = _parse_hhmm(gio_bat_dau)
    h2, m2 = _parse_hhmm(gio_ket_thuc)
    start = d.replace(hour=h1, minute=m1, second=0)
    end = d.replace(hour=h2, minute=m2, second=0)
    if end <= start:
        end = end + timedelta(days=1)
    return (end - start).total_seconds() / 3600.0


def ky_luong_15(today: date) -> tuple[date, date]:
    """
    Quy ước kỳ lương:
    - Nếu hôm nay >= 15: kỳ hiện tại = 16 tháng trước -> 15 tháng này
    - Nếu hôm nay < 15: kỳ gần nhất = 16 tháng trước nữa -> 15 tháng trước
    """
    if today.day >= 15:
        end = today.replace(day=15)
    else:
        prev_month_last = (today.replace(day=1) - timedelta(days=1))
        end = prev_month_last.replace(day=15)
    start = (end.replace(day=1) - timedelta(days=1)).replace(day=16)
    return start, end


class BangLuongModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_paid_recent(self, limit: int = 200) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            """SELECT b.id, b.nhan_vien_id, n.ten, b.tu_ngay, b.den_ngay, b.tong_gio, b.tong_tien,
                      b.da_tra, b.ngay_tra, b.ghi_chu
               FROM bang_luong b
               JOIN nhan_vien n ON n.id = b.nhan_vien_id
               ORDER BY b.id DESC
               LIMIT ?""",
            (limit,),
        )
        return cur.fetchall()

    def da_tra_ky(self, tu_ngay: str, den_ngay: str) -> bool:
        cur = self._conn.execute(
            """SELECT COUNT(1) AS c
               FROM bang_luong
               WHERE tu_ngay = ? AND den_ngay = ? AND da_tra = 1""",
            (tu_ngay, den_ngay),
        )
        return int(cur.fetchone()[0]) > 0

    def tinh_bang_luong_tu_phan_cong(self, tu_ngay: str, den_ngay: str) -> list[BangLuongDong]:
        cur = self._conn.execute(
            """SELECT pc.nhan_vien_id, n.ten AS nhan_vien_ten,
                      COALESCE(cv.ten, n.chuc_vu, '') AS chuc_vu_ten,
                      n.luong_gio,
                      ca.gio_bat_dau, ca.gio_ket_thuc, ca.he_so AS ca_he_so,
                      COALESCE(cv.he_so, 1.0) AS cv_he_so,
                      pc.ngay
               FROM phan_cong_ca pc
               JOIN nhan_vien n ON n.id = pc.nhan_vien_id
               JOIN ca_lam ca ON ca.id = pc.ca_id
               LEFT JOIN chuc_vu cv ON cv.id = n.chuc_vu_id
               WHERE date(pc.ngay) >= date(?) AND date(pc.ngay) <= date(?)
               ORDER BY pc.nhan_vien_id""",
            (tu_ngay, den_ngay),
        )
        by_nv: dict[int, BangLuongDong] = {}
        for r in cur.fetchall():
            nv_id = int(r["nhan_vien_id"])
            luong_gio = float(r["luong_gio"] or 0.0)
            so_gio = _hours_of_shift(str(r["ngay"]), str(r["gio_bat_dau"]), str(r["gio_ket_thuc"]))
            ca_he_so = float(r["ca_he_so"] or 1.0)
            cv_he_so = float(r["cv_he_so"] or 1.0)
            tien = so_gio * luong_gio * ca_he_so * cv_he_so
            if nv_id not in by_nv:
                by_nv[nv_id] = BangLuongDong(
                    nhan_vien_id=nv_id,
                    ten=str(r["nhan_vien_ten"] or ""),
                    chuc_vu=str(r["chuc_vu_ten"] or ""),
                    luong_gio=luong_gio,
                    tong_gio=0.0,
                    tong_tien=0.0,
                )
            by_nv[nv_id].tong_gio += so_gio
            by_nv[nv_id].tong_tien += tien
        return sorted(by_nv.values(), key=lambda x: x.tong_tien, reverse=True)

    def chot_va_tra_luong(
        self,
        tu_ngay: str,
        den_ngay: str,
        rows: list[BangLuongDong],
        ghi_chu: str | None = None,
    ) -> int:
        """Insert nhiều dòng bang_luong (da_tra=1) trong một transaction."""
        now = datetime.now().isoformat(timespec="seconds")
        conn = self._conn
        if self.da_tra_ky(tu_ngay, den_ngay):
            raise ValueError("Kỳ lương này đã được trả trước đó.")
        try:
            conn.execute("BEGIN")
            for r in rows:
                conn.execute(
                    """INSERT INTO bang_luong (nhan_vien_id, tu_ngay, den_ngay, tong_gio, tong_tien, ngay_tao, da_tra, ngay_tra, ghi_chu)
                       VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)""",
                    (
                        r.nhan_vien_id,
                        tu_ngay,
                        den_ngay,
                        round(r.tong_gio, 4),
                        round(r.tong_tien, 0),
                        now,
                        now,
                        (ghi_chu or "").strip() or None,
                    ),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return len(rows)

