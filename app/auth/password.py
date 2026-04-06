"""Băm mật khẩu PBKDF2 (thư viện chuẩn, không thêm dependency)."""

from __future__ import annotations

import hashlib
import secrets


def hash_password(plain: str) -> tuple[str, str]:
    """Trả về (salt_hex, hash_hex)."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, 100_000)
    return salt.hex(), dk.hex()


def verify_password(plain: str, salt_hex: str, hash_hex: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, 100_000)
    return secrets.compare_digest(dk, expected)
