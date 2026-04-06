"""Kết nối SQLite và khởi tạo schema."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def get_default_db_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "data" / "billiard.db"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ban (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten_ban TEXT NOT NULL,
    loai_ban TEXT NOT NULL DEFAULT '',
    trang_thai TEXT CHECK(trang_thai IN ('trong','dang_choi')) DEFAULT 'trong',
    gia_gio REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS nhan_vien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL,
    so_dien_thoai TEXT,
    luong REAL,
    chuc_vu TEXT
);
CREATE TABLE IF NOT EXISTS phien_choi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ban_id INTEGER,
    nhan_vien_id INTEGER,
    gio_bat_dau DATETIME,
    gio_ket_thuc DATETIME,
    FOREIGN KEY (ban_id) REFERENCES ban(id),
    FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id)
);
CREATE TABLE IF NOT EXISTS dich_vu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL,
    gia REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS hoa_don (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phien_id INTEGER,
    thoi_gian_choi REAL,
    tien_ban REAL,
    tien_dich_vu REAL,
    tong_tien REAL,
    ngay_tao DATETIME,
    FOREIGN KEY (phien_id) REFERENCES phien_choi(id)
);
CREATE TABLE IF NOT EXISTS chi_tiet_hoa_don (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hoa_don_id INTEGER,
    dich_vu_id INTEGER,
    so_luong INTEGER,
    thanh_tien REAL,
    FOREIGN KEY (hoa_don_id) REFERENCES hoa_don(id),
    FOREIGN KEY (dich_vu_id) REFERENCES dich_vu(id)
);
CREATE TABLE IF NOT EXISTS tai_khoan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten_dang_nhap TEXT NOT NULL UNIQUE,
    mat_khau_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    ho_ten TEXT NOT NULL DEFAULT '',
    vai_tro TEXT NOT NULL CHECK (vai_tro IN ('admin', 'nhan_vien')),
    ngay_tao DATETIME
);
"""


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def init_schema(self) -> None:
        conn = self.connect()
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        self._migrate_ban_loai_ban(conn)

    def _migrate_ban_loai_ban(self, conn: sqlite3.Connection) -> None:
        cur = conn.execute("PRAGMA table_info(ban)")
        cols = {row[1] for row in cur.fetchall()}
        if "loai_ban" not in cols:
            conn.execute("ALTER TABLE ban ADD COLUMN loai_ban TEXT DEFAULT ''")
            conn.execute("UPDATE ban SET loai_ban = '' WHERE loai_ban IS NULL")
            conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
