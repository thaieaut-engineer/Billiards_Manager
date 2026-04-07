"""Model: bàn bi-a."""

from __future__ import annotations

import sqlite3


class BanModel:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @staticmethod
    def _coalesce_loai_name_expr() -> str:
        # Prefer loai_ban.ten; fallback to legacy ban.loai_ban
        return "COALESCE(lb.ten, TRIM(COALESCE(b.loai_ban, '')))"

    @staticmethod
    def _gia_hieu_luc_expr() -> str:
        # Ưu tiên giá riêng; nếu không có thì giá mặc định loại (nếu >0); nếu vẫn không có thì dùng giá legacy của bàn.
        return (
            "COALESCE("
            "b.gia_gio_rieng, "
            "CASE WHEN lb.gia_gio_mac_dinh IS NOT NULL AND lb.gia_gio_mac_dinh > 0 THEN lb.gia_gio_mac_dinh END, "
            "b.gia_gio"
            ")"
        )

    def _ten_key(self, ten_ban: str) -> str:
        return ten_ban.strip().lower()

    def exists_ten(self, ten_ban: str, exclude_id: int | None = None) -> bool:
        key = self._ten_key(ten_ban)
        if not key:
            return False
        if exclude_id is None:
            cur = self._conn.execute(
                "SELECT 1 FROM ban WHERE LOWER(TRIM(ten_ban)) = ? LIMIT 1",
                (key,),
            )
        else:
            cur = self._conn.execute(
                "SELECT 1 FROM ban WHERE LOWER(TRIM(ten_ban)) = ? AND id != ? LIMIT 1",
                (key, int(exclude_id)),
            )
        return cur.fetchone() is not None

    def list_all(self, loc_loai: str | None = None) -> list[sqlite3.Row]:
        """loc_loai: None = tất cả; '' = chỉ bàn chưa gán loại; chuỗi khác = khớp loại."""
        lo = self._coalesce_loai_name_expr()
        gia = self._gia_hieu_luc_expr()
        base = (
            "SELECT b.id, b.ten_ban, "
            f"{lo} AS loai_ban, "
            "b.trang_thai, "
            f"{gia} AS gia_gio, "
            "b.loai_ban_id, b.gia_gio_rieng, "
            "COALESCE(lb.sale_percent, 0) AS sale_percent "
            "FROM ban b "
            "LEFT JOIN loai_ban lb ON lb.id = b.loai_ban_id "
        )
        if loc_loai is None:
            cur = self._conn.execute(base + "ORDER BY b.id")
        elif loc_loai == "":
            cur = self._conn.execute(
                base + f"WHERE TRIM(COALESCE({lo}, '')) = '' ORDER BY b.id"
            )
        else:
            cur = self._conn.execute(
                base + f"WHERE TRIM({lo}) = ? ORDER BY b.id",
                (loc_loai.strip(),),
            )
        return cur.fetchall()

    def distinct_loai_ban(self) -> list[str]:
        lo = self._coalesce_loai_name_expr()
        cur = self._conn.execute(
            f"""SELECT DISTINCT TRIM({lo}) AS lo
                FROM ban b
                LEFT JOIN loai_ban lb ON lb.id = b.loai_ban_id
                WHERE TRIM(COALESCE({lo}, '')) != ''
                ORDER BY lo COLLATE NOCASE"""
        )
        return [row[0] for row in cur.fetchall()]

    def has_any_empty_loai(self) -> bool:
        lo = self._coalesce_loai_name_expr()
        cur = self._conn.execute(
            f"""SELECT 1
                FROM ban b
                LEFT JOIN loai_ban lb ON lb.id = b.loai_ban_id
                WHERE TRIM(COALESCE({lo}, '')) = ''
                LIMIT 1"""
        )
        return cur.fetchone() is not None

    def get(self, ban_id: int) -> sqlite3.Row | None:
        lo = self._coalesce_loai_name_expr()
        gia = self._gia_hieu_luc_expr()
        cur = self._conn.execute(
            "SELECT b.id, b.ten_ban, "
            f"{lo} AS loai_ban, "
            "b.trang_thai, "
            f"{gia} AS gia_gio, "
            "b.loai_ban_id, b.gia_gio_rieng, b.gia_gio AS gia_gio_legacy, "
            "COALESCE(lb.gia_gio_mac_dinh, 0) AS gia_gio_mac_dinh, "
            "COALESCE(lb.sale_percent, 0) AS sale_percent "
            "FROM ban b "
            "LEFT JOIN loai_ban lb ON lb.id = b.loai_ban_id "
            "WHERE b.id = ?",
            (ban_id,),
        )
        return cur.fetchone()

    def create(
        self,
        ten_ban: str,
        gia_gio: float,
        loai_ban: str = "",
        *,
        loai_ban_id: int | None = None,
        gia_gio_rieng: float | None = None,
    ) -> int:
        ten = ten_ban.strip()
        if self.exists_ten(ten):
            raise ValueError("Tên bàn đã tồn tại.")
        loai_txt = loai_ban.strip()
        if loai_ban_id is not None and not loai_txt:
            cur = self._conn.execute("SELECT ten FROM loai_ban WHERE id = ?", (int(loai_ban_id),))
            row = cur.fetchone()
            loai_txt = (row[0] if row else "").strip()
        cur = self._conn.execute(
            """INSERT INTO ban (ten_ban, trang_thai, gia_gio, loai_ban, loai_ban_id, gia_gio_rieng)
               VALUES (?, 'trong', ?, ?, ?, ?)""",
            (
                ten,
                float(gia_gio),
                loai_txt,
                int(loai_ban_id) if loai_ban_id is not None else None,
                float(gia_gio_rieng) if gia_gio_rieng is not None else None,
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update(
        self,
        ban_id: int,
        ten_ban: str,
        gia_gio: float,
        loai_ban: str = "",
        *,
        loai_ban_id: int | None = None,
        gia_gio_rieng: float | None = None,
    ) -> None:
        ten = ten_ban.strip()
        if self.exists_ten(ten, exclude_id=int(ban_id)):
            raise ValueError("Tên bàn đã tồn tại.")
        loai_txt = loai_ban.strip()
        if loai_ban_id is not None and not loai_txt:
            cur = self._conn.execute("SELECT ten FROM loai_ban WHERE id = ?", (int(loai_ban_id),))
            row = cur.fetchone()
            loai_txt = (row[0] if row else "").strip()
        self._conn.execute(
            """UPDATE ban
               SET ten_ban = ?,
                   gia_gio = ?,
                   loai_ban = ?,
                   loai_ban_id = ?,
                   gia_gio_rieng = ?
               WHERE id = ?""",
            (
                ten,
                float(gia_gio),
                loai_txt,
                int(loai_ban_id) if loai_ban_id is not None else None,
                float(gia_gio_rieng) if gia_gio_rieng is not None else None,
                int(ban_id),
            ),
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
        lo = self._coalesce_loai_name_expr()
        gia = self._gia_hieu_luc_expr()
        cur = self._conn.execute(
            "SELECT b.id, b.ten_ban, "
            f"{lo} AS loai_ban, "
            "b.trang_thai, "
            f"{gia} AS gia_gio, "
            "b.loai_ban_id, b.gia_gio_rieng, "
            "COALESCE(lb.sale_percent, 0) AS sale_percent "
            "FROM ban b "
            "LEFT JOIN loai_ban lb ON lb.id = b.loai_ban_id "
            "WHERE b.trang_thai = 'trong' "
            "ORDER BY b.id"
        )
        return cur.fetchall()
