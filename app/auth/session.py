"""Phiên đăng nhập hiện tại."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Session:
    user_id: int
    ten_dang_nhap: str
    ho_ten: str
    vai_tro: str  # admin | nhan_vien

    def is_admin(self) -> bool:
        return self.vai_tro == "admin"
