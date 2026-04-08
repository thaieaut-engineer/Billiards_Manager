"""Kết nối SQLite và khởi tạo schema."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


def get_default_db_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "data" / "billiard.db"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS loai_ban (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL UNIQUE COLLATE NOCASE,
    gia_gio_mac_dinh REAL NOT NULL DEFAULT 0,
    sale_percent REAL NOT NULL DEFAULT 0,
    ngay_tao DATETIME
);
CREATE TABLE IF NOT EXISTS ban (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten_ban TEXT NOT NULL,
    loai_ban TEXT NOT NULL DEFAULT '',
    loai_ban_id INTEGER,
    trang_thai TEXT CHECK(trang_thai IN ('trong','dang_choi')) DEFAULT 'trong',
    gia_gio REAL NOT NULL,
    gia_gio_rieng REAL,
    FOREIGN KEY (loai_ban_id) REFERENCES loai_ban(id)
);
CREATE TABLE IF NOT EXISTS nhan_vien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL,
    so_dien_thoai TEXT,
    luong REAL,
    chuc_vu TEXT
);
CREATE TABLE IF NOT EXISTS chuc_vu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL UNIQUE COLLATE NOCASE,
    he_so REAL NOT NULL DEFAULT 1.0,
    ngay_tao DATETIME
);
CREATE TABLE IF NOT EXISTS ca_lam (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL UNIQUE COLLATE NOCASE,
    gio_bat_dau TEXT NOT NULL,  -- 'HH:MM'
    gio_ket_thuc TEXT NOT NULL, -- 'HH:MM' (có thể qua ngày)
    he_so REAL NOT NULL DEFAULT 1.0,
    ngay_tao DATETIME
);
CREATE TABLE IF NOT EXISTS cham_cong (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nhan_vien_id INTEGER NOT NULL,
    ca_id INTEGER NOT NULL,
    ngay DATE NOT NULL,         -- 'YYYY-MM-DD'
    gio_vao DATETIME,           -- 'YYYY-MM-DDTHH:MM:SS'
    gio_ra DATETIME,            -- 'YYYY-MM-DDTHH:MM:SS'
    so_gio REAL,                -- nếu NULL thì tính từ giờ vào/ra hoặc theo ca
    ghi_chu TEXT,
    FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
    FOREIGN KEY (ca_id) REFERENCES ca_lam(id)
);
CREATE TABLE IF NOT EXISTS phan_cong_ca (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nhan_vien_id INTEGER NOT NULL,
    ca_id INTEGER NOT NULL,
    ngay DATE NOT NULL,         -- 'YYYY-MM-DD'
    ghi_chu TEXT,
    ngay_tao DATETIME,
    FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
    FOREIGN KEY (ca_id) REFERENCES ca_lam(id)
);
CREATE TABLE IF NOT EXISTS bang_luong (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nhan_vien_id INTEGER NOT NULL,
    tu_ngay DATE NOT NULL,
    den_ngay DATE NOT NULL,
    tong_gio REAL NOT NULL,
    tong_tien REAL NOT NULL,
    ngay_tao DATETIME,
    da_tra INTEGER NOT NULL DEFAULT 0,
    ngay_tra DATETIME,
    ghi_chu TEXT,
    FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id)
);
CREATE TABLE IF NOT EXISTS phien_choi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ban_id INTEGER,
    nhan_vien_id INTEGER,
    gio_bat_dau DATETIME,
    gio_ket_thuc DATETIME,
    gia_gio_ap_dung REAL,
    sale_percent_ap_dung REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (ban_id) REFERENCES ban(id),
    FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id)
);
CREATE TABLE IF NOT EXISTS danh_muc_dich_vu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL UNIQUE COLLATE NOCASE,
    ngay_tao DATETIME
);
CREATE TABLE IF NOT EXISTS dich_vu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL,
    gia REAL NOT NULL,
    danh_muc_id INTEGER NOT NULL,
    FOREIGN KEY (danh_muc_id) REFERENCES danh_muc_dich_vu(id)
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
        self._migrate_loai_ban_and_pricing(conn)
        self._migrate_phien_pricing(conn)
        self._migrate_nhan_su(conn)
        self._migrate_danh_muc_dich_vu(conn)

    def _try_drop_column(
        self, conn: sqlite3.Connection, table: str, column: str
    ) -> None:
        try:
            conn.execute(f'ALTER TABLE "{table}" DROP COLUMN "{column}"')
        except sqlite3.OperationalError:
            pass

    def _migrate_danh_muc_dich_vu(self, conn: sqlite3.Connection) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS danh_muc_dich_vu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten TEXT NOT NULL UNIQUE COLLATE NOCASE,
                ngay_tao DATETIME
            )"""
        )
        cur = conn.execute("SELECT COUNT(1) AS c FROM danh_muc_dich_vu")
        if int(cur.fetchone()[0]) == 0:
            for t in ("Đồ ăn", "Thức uống", "Đồ ăn vặt", "Khác"):
                conn.execute(
                    "INSERT INTO danh_muc_dich_vu (ten, ngay_tao) VALUES (?, ?)",
                    (t, now),
                )
            conn.commit()

        cur = conn.execute("PRAGMA table_info(dich_vu)")
        cols = {row[1] for row in cur.fetchall()}
        if "danh_muc_id" in cols:
            if "danh_muc" in cols:
                self._try_drop_column(conn, "dich_vu", "danh_muc")
                conn.commit()
            return

        cur = conn.execute(
            "SELECT id FROM danh_muc_dich_vu WHERE ten = 'Khác' LIMIT 1"
        )
        row_khac = cur.fetchone()
        khac_id = int(row_khac[0]) if row_khac else None
        if khac_id is None:
            conn.execute(
                "INSERT INTO danh_muc_dich_vu (ten, ngay_tao) VALUES ('Khác', ?)",
                (now,),
            )
            khac_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

        if "danh_muc" in cols:
            cur = conn.execute(
                """SELECT DISTINCT TRIM(COALESCE(danh_muc, '')) AS t
                   FROM dich_vu
                   WHERE TRIM(COALESCE(danh_muc, '')) != ''"""
            )
            for (t,) in cur.fetchall():
                conn.execute(
                    "INSERT OR IGNORE INTO danh_muc_dich_vu (ten, ngay_tao) VALUES (?, ?)",
                    (t, now),
                )
            conn.execute(
                "ALTER TABLE dich_vu ADD COLUMN danh_muc_id INTEGER REFERENCES danh_muc_dich_vu(id)"
            )
            conn.execute(
                """UPDATE dich_vu SET danh_muc_id = (
                    SELECT m.id FROM danh_muc_dich_vu m
                    WHERE LOWER(m.ten) = LOWER(TRIM(dich_vu.danh_muc))
                ) WHERE danh_muc_id IS NULL"""
            )
            conn.execute(
                "UPDATE dich_vu SET danh_muc_id = ? WHERE danh_muc_id IS NULL",
                (khac_id,),
            )
            self._try_drop_column(conn, "dich_vu", "danh_muc")
        else:
            conn.execute(
                "ALTER TABLE dich_vu ADD COLUMN danh_muc_id INTEGER REFERENCES danh_muc_dich_vu(id)"
            )
            conn.execute(
                "UPDATE dich_vu SET danh_muc_id = ? WHERE danh_muc_id IS NULL",
                (khac_id,),
            )
        conn.commit()

    def _migrate_ban_loai_ban(self, conn: sqlite3.Connection) -> None:
        cur = conn.execute("PRAGMA table_info(ban)")
        cols = {row[1] for row in cur.fetchall()}
        if "loai_ban" not in cols:
            conn.execute("ALTER TABLE ban ADD COLUMN loai_ban TEXT DEFAULT ''")
            conn.execute("UPDATE ban SET loai_ban = '' WHERE loai_ban IS NULL")
            conn.commit()

    def _migrate_loai_ban_and_pricing(self, conn: sqlite3.Connection) -> None:
        # 1) Ensure columns exist on ban
        cur = conn.execute("PRAGMA table_info(ban)")
        cols = {row[1] for row in cur.fetchall()}
        if "loai_ban_id" not in cols:
            conn.execute("ALTER TABLE ban ADD COLUMN loai_ban_id INTEGER")
        if "gia_gio_rieng" not in cols:
            conn.execute("ALTER TABLE ban ADD COLUMN gia_gio_rieng REAL")

        # 2) Ensure loai_ban table exists (for older DB created before SCHEMA_SQL update)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS loai_ban (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten TEXT NOT NULL UNIQUE COLLATE NOCASE,
                gia_gio_mac_dinh REAL NOT NULL DEFAULT 0,
                sale_percent REAL NOT NULL DEFAULT 0,
                ngay_tao DATETIME
            )"""
        )

        # 3) Migrate legacy ban.loai_ban (TEXT) -> loai_ban row + ban.loai_ban_id
        # Note: do NOT overwrite existing loai_ban_id if already set.
        cur = conn.execute(
            """SELECT DISTINCT TRIM(COALESCE(loai_ban, '')) AS lo
               FROM ban
               WHERE TRIM(COALESCE(loai_ban, '')) != ''"""
        )
        los = [row[0] for row in cur.fetchall() if row[0]]
        if not los:
            conn.commit()
            return
        now = datetime.now().isoformat(timespec="seconds")
        for lo in los:
            # Create type if missing; default price 0 to avoid changing legacy pricing.
            conn.execute(
                "INSERT OR IGNORE INTO loai_ban (ten, gia_gio_mac_dinh, sale_percent, ngay_tao) VALUES (?, 0, 0, ?)",
                (lo, now),
            )
            # Map ban rows (only those not mapped yet)
            conn.execute(
                """UPDATE ban
                   SET loai_ban_id = (SELECT id FROM loai_ban WHERE ten = ?)
                   WHERE loai_ban_id IS NULL AND TRIM(COALESCE(loai_ban, '')) = ?""",
                (lo, lo),
            )
        conn.commit()

    def _migrate_phien_pricing(self, conn: sqlite3.Connection) -> None:
        cur = conn.execute("PRAGMA table_info(phien_choi)")
        cols = {row[1] for row in cur.fetchall()}
        if "gia_gio_ap_dung" not in cols:
            conn.execute("ALTER TABLE phien_choi ADD COLUMN gia_gio_ap_dung REAL")
        if "sale_percent_ap_dung" not in cols:
            conn.execute(
                "ALTER TABLE phien_choi ADD COLUMN sale_percent_ap_dung REAL NOT NULL DEFAULT 0"
            )
        conn.commit()

    def _migrate_nhan_su(self, conn: sqlite3.Connection) -> None:
        # 1) Ensure columns exist on nhan_vien (giữ lại cột legacy luong/chuc_vu)
        cur = conn.execute("PRAGMA table_info(nhan_vien)")
        cols = {row[1] for row in cur.fetchall()}
        if "luong_gio" not in cols:
            conn.execute("ALTER TABLE nhan_vien ADD COLUMN luong_gio REAL")
        if "chuc_vu_id" not in cols:
            conn.execute("ALTER TABLE nhan_vien ADD COLUMN chuc_vu_id INTEGER")

        # 2) Ensure tables exist (trường hợp DB cũ thiếu do SCHEMA_SQL chưa chạy)
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS chuc_vu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten TEXT NOT NULL UNIQUE COLLATE NOCASE,
                he_so REAL NOT NULL DEFAULT 1.0,
                ngay_tao DATETIME
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS ca_lam (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten TEXT NOT NULL UNIQUE COLLATE NOCASE,
                gio_bat_dau TEXT NOT NULL,
                gio_ket_thuc TEXT NOT NULL,
                he_so REAL NOT NULL DEFAULT 1.0,
                ngay_tao DATETIME
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS cham_cong (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nhan_vien_id INTEGER NOT NULL,
                ca_id INTEGER NOT NULL,
                ngay DATE NOT NULL,
                gio_vao DATETIME,
                gio_ra DATETIME,
                so_gio REAL,
                ghi_chu TEXT,
                FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
                FOREIGN KEY (ca_id) REFERENCES ca_lam(id)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS phan_cong_ca (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nhan_vien_id INTEGER NOT NULL,
                ca_id INTEGER NOT NULL,
                ngay DATE NOT NULL,
                ghi_chu TEXT,
                ngay_tao DATETIME,
                FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
                FOREIGN KEY (ca_id) REFERENCES ca_lam(id)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS bang_luong (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nhan_vien_id INTEGER NOT NULL,
                tu_ngay DATE NOT NULL,
                den_ngay DATE NOT NULL,
                tong_gio REAL NOT NULL,
                tong_tien REAL NOT NULL,
                ngay_tao DATETIME,
                da_tra INTEGER NOT NULL DEFAULT 0,
                ngay_tra DATETIME,
                ghi_chu TEXT,
                FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id)
            )"""
        )

        # 2b) Ensure new columns exist on bang_luong (DB cũ tạo trước khi thêm cột)
        cur = conn.execute("PRAGMA table_info(bang_luong)")
        cols = {row[1] for row in cur.fetchall()}
        if "da_tra" not in cols:
            conn.execute("ALTER TABLE bang_luong ADD COLUMN da_tra INTEGER NOT NULL DEFAULT 0")
        if "ngay_tra" not in cols:
            conn.execute("ALTER TABLE bang_luong ADD COLUMN ngay_tra DATETIME")
        if "ghi_chu" not in cols:
            conn.execute("ALTER TABLE bang_luong ADD COLUMN ghi_chu TEXT")

        # 3) Seed default shifts if empty
        cur = conn.execute("SELECT COUNT(1) AS c FROM ca_lam")
        if int(cur.fetchone()[0]) == 0:
            conn.execute(
                "INSERT INTO ca_lam (ten, gio_bat_dau, gio_ket_thuc, he_so, ngay_tao) VALUES (?, ?, ?, ?, ?)",
                ("Ca ngày", "08:00", "16:00", 1.0, now),
            )
            conn.execute(
                "INSERT INTO ca_lam (ten, gio_bat_dau, gio_ket_thuc, he_so, ngay_tao) VALUES (?, ?, ?, ?, ?)",
                ("Ca chiều", "16:00", "22:00", 1.0, now),
            )
            conn.execute(
                "INSERT INTO ca_lam (ten, gio_bat_dau, gio_ket_thuc, he_so, ngay_tao) VALUES (?, ?, ?, ?, ?)",
                ("Ca đêm", "22:00", "06:00", 1.3, now),
            )

        # 4) Migrate legacy text chuc_vu -> chuc_vu table and set nhan_vien.chuc_vu_id
        cur = conn.execute(
            """SELECT DISTINCT TRIM(COALESCE(chuc_vu, '')) AS cv
               FROM nhan_vien
               WHERE TRIM(COALESCE(chuc_vu, '')) != ''"""
        )
        cvs = [row[0] for row in cur.fetchall() if row[0]]
        for cv in cvs:
            conn.execute(
                "INSERT OR IGNORE INTO chuc_vu (ten, he_so, ngay_tao) VALUES (?, 1.0, ?)",
                (cv, now),
            )
            conn.execute(
                """UPDATE nhan_vien
                   SET chuc_vu_id = (SELECT id FROM chuc_vu WHERE ten = ?)
                   WHERE chuc_vu_id IS NULL AND TRIM(COALESCE(chuc_vu, '')) = ?""",
                (cv, cv),
            )

        # 5) If luong_gio missing but luong(month) exists, leave NULL (tùy bạn nhập lại)
        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
