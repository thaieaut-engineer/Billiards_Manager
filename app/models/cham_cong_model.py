"""Model: chấm công (legacy) + tính lương theo giờ và hệ số ca/chức vụ.

Hiện tại app dùng `phan_cong_ca` cho phân ca/tăng ca và tính lương theo kỳ 15.
File này vẫn giữ để tương thích nếu bạn muốn chấm theo giờ vào/ra.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class LuongDong:
    nhan_vien_id: int
    ten: str
    chuc_vu: str
    luong_gio: float
    tong_gio: float
    tong_tien: float


def _parse_hhmm(s: str) -> tuple[int, int]:
    hh, mm = s.strip().split(":")
    return int(hh), int(mm)


class ChamCongModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_by_date_range(self, tu_ngay: str, den_ngay: str) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            """SELECT cc.id, cc.ngay, cc.gio_vao, cc.gio_ra, cc.so_gio, cc.ghi_chu,
                      n.id AS nhan_vien_id, n.ten AS nhan_vien_ten,
                      COALESCE(cv.ten, n.chuc_vu, '') AS chuc_vu_ten,
                      n.luong_gio,
                      ca.id AS ca_id, ca.ten AS ca_ten, ca.gio_bat_dau, ca.gio_ket_thuc, ca.he_so AS ca_he_so,
                      COALESCE(cv.he_so, 1.0) AS cv_he_so
               FROM cham_cong cc
               JOIN nhan_vien n ON n.id = cc.nhan_vien_id
               JOIN ca_lam ca ON ca.id = cc.ca_id
               LEFT JOIN chuc_vu cv ON cv.id = n.chuc_vu_id
               WHERE date(cc.ngay) >= date(?) AND date(cc.ngay) <= date(?)
               ORDER BY cc.ngay DESC, cc.id DESC""",
            (tu_ngay, den_ngay),
        )
        return cur.fetchall()

    def create_from_ca(
        self,
        nhan_vien_id: int,
        ca_id: int,
        ngay: str,
        ghi_chu: str | None = None,
    ) -> int:
        ca = self._conn.execute(
            "SELECT gio_bat_dau, gio_ket_thuc FROM ca_lam WHERE id = ?",
            (ca_id,),
        ).fetchone()
        if not ca:
            raise ValueError("Ca làm không tồn tại.")
        hh1, mm1 = _parse_hhmm(ca["gio_bat_dau"])
        hh2, mm2 = _parse_hhmm(ca["gio_ket_thuc"])
        d = datetime.fromisoformat(ngay)
        vao = d.replace(hour=hh1, minute=mm1, second=0)
        ra = d.replace(hour=hh2, minute=mm2, second=0)
        if ra <= vao:
            ra = ra + timedelta(days=1)
        so_gio = (ra - vao).total_seconds() / 3600.0
        cur = self._conn.execute(
            """INSERT INTO cham_cong (nhan_vien_id, ca_id, ngay, gio_vao, gio_ra, so_gio, ghi_chu)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                nhan_vien_id,
                ca_id,
                ngay,
                vao.isoformat(timespec="seconds"),
                ra.isoformat(timespec="seconds"),
                round(so_gio, 4),
                (ghi_chu or "").strip() or None,
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def delete(self, cham_cong_id: int) -> None:
        self._conn.execute("DELETE FROM cham_cong WHERE id = ?", (cham_cong_id,))
        self._conn.commit()

    def tinh_luong(self, tu_ngay: str, den_ngay: str) -> list[LuongDong]:
        rows = self.list_by_date_range(tu_ngay, den_ngay)
        by_nv: dict[int, LuongDong] = {}
        for r in rows:
            nv_id = int(r["nhan_vien_id"])
            luong_gio = float(r["luong_gio"] or 0.0)
            so_gio = float(r["so_gio"] or 0.0)
            ca_he_so = float(r["ca_he_so"] or 1.0)
            cv_he_so = float(r["cv_he_so"] or 1.0)
            tien = so_gio * luong_gio * ca_he_so * cv_he_so
            if nv_id not in by_nv:
                by_nv[nv_id] = LuongDong(
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

