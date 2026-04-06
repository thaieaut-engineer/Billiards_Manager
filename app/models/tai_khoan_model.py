"""Model tài khoản đăng nhập."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from app.auth import Session, hash_password, verify_password


class TaiKhoanModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM tai_khoan")
        return int(cur.fetchone()[0])

    def list_all(self) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            "SELECT id, ten_dang_nhap, ho_ten, vai_tro, ngay_tao FROM tai_khoan ORDER BY id"
        )
        return cur.fetchall()

    def get_by_id(self, user_id: int) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT id, ten_dang_nhap, mat_khau_hash, salt, ho_ten, vai_tro, ngay_tao FROM tai_khoan WHERE id = ?",
            (user_id,),
        )
        return cur.fetchone()

    def count_admins(self) -> int:
        cur = self._conn.execute(
            "SELECT COUNT(*) FROM tai_khoan WHERE vai_tro = 'admin'"
        )
        return int(cur.fetchone()[0])

    def set_password(self, user_id: int, mat_khau: str) -> None:
        if len(mat_khau) < 4:
            raise ValueError("Mật khẩu ít nhất 4 ký tự.")
        salt, h = hash_password(mat_khau)
        self._conn.execute(
            "UPDATE tai_khoan SET mat_khau_hash = ?, salt = ? WHERE id = ?",
            (h, salt, user_id),
        )
        self._conn.commit()

    def delete(self, user_id: int) -> None:
        self._conn.execute("DELETE FROM tai_khoan WHERE id = ?", (user_id,))
        self._conn.commit()

    def get_by_username(self, ten_dang_nhap: str) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT id, ten_dang_nhap, mat_khau_hash, salt, ho_ten, vai_tro FROM tai_khoan WHERE LOWER(ten_dang_nhap) = LOWER(?)",
            (ten_dang_nhap.strip(),),
        )
        return cur.fetchone()

    def verify_login(self, ten_dang_nhap: str, mat_khau: str) -> Session | None:
        row = self.get_by_username(ten_dang_nhap)
        if row is None:
            return None
        if not verify_password(mat_khau, row["salt"], row["mat_khau_hash"]):
            return None
        return Session(
            user_id=int(row["id"]),
            ten_dang_nhap=row["ten_dang_nhap"],
            ho_ten=row["ho_ten"] or "",
            vai_tro=row["vai_tro"],
        )

    def create(
        self,
        ten_dang_nhap: str,
        mat_khau: str,
        ho_ten: str,
        vai_tro: str,
    ) -> int:
        ten = ten_dang_nhap.strip()
        if not ten:
            raise ValueError("Tên đăng nhập không được trống.")
        if vai_tro not in ("admin", "nhan_vien"):
            raise ValueError("Vai trò không hợp lệ.")
        if self.get_by_username(ten):
            raise ValueError("Tên đăng nhập đã tồn tại.")
        salt, h = hash_password(mat_khau)
        now = datetime.now().isoformat(timespec="seconds")
        cur = self._conn.execute(
            """INSERT INTO tai_khoan (ten_dang_nhap, mat_khau_hash, salt, ho_ten, vai_tro, ngay_tao)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ten, h, salt, ho_ten.strip(), vai_tro, now),
        )
        self._conn.commit()
        return int(cur.lastrowid)
