"""Controller: kết nối View với các Model (MVC)."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QMessageBox,
    QTableWidgetItem,
)

from app.auth import Session
from app.database import Database
from app.dialogs import ChangePasswordDialog, RegisterDialog
from app.widgets import BanTile
from app.models import (
    BanModel,
    CaLamModel,
    ChamCongModel,
    ChucVuModel,
    BangLuongModel,
    DichVuModel,
    HoaDonModel,
    LoaiBanModel,
    NhanVienModel,
    PhanCongModel,
    PhienChoiModel,
    TaiKhoanModel,
)
from app.models.hoa_don_model import ChiTietLine
from app.views import MainWindowView


def _money(v: float) -> str:
    return f"{int(round(v)):,}".replace(",", ".")


@dataclass
class _TamDichVu:
    dich_vu_id: int
    ten: str
    don_gia: float
    so_luong: int

    @property
    def thanh_tien(self) -> float:
        return self.don_gia * self.so_luong


class MainController:
    def __init__(self, view: MainWindowView, database: Database, session: Session) -> None:
        self._view = view
        self._db = database
        self._conn = database.connect()
        self._session = session
        self._ban = BanModel(self._conn)
        self._loai_ban = LoaiBanModel(self._conn)
        self._nv = NhanVienModel(self._conn)
        self._chuc_vu = ChucVuModel(self._conn)
        self._ca_lam = CaLamModel(self._conn)
        self._cham_cong = ChamCongModel(self._conn)
        self._phan_cong = PhanCongModel(self._conn)
        self._bang_luong = BangLuongModel(self._conn)
        self._dv = DichVuModel(self._conn)
        self._phien = PhienChoiModel(self._conn)
        self._hd = HoaDonModel(self._conn)
        self._tai_khoan = TaiKhoanModel(self._conn)
        self._tam_dich_vu_theo_phien: dict[int, list[_TamDichVu]] = {}
        self._phien_dang_chon: int | None = None
        self._phien_ban_tiles: dict[int, BanTile] = {}
        self._ban_trong_dang_chon: int | None = None
        self._filter_loai: str | None = None  # None=tất cả; ''=chưa gán loại
        self._on_logout: Callable[[], None] | None = None

    def set_logout_handler(self, handler: Callable[[], None]) -> None:
        self._on_logout = handler

    def setup(self) -> None:
        self._init_tables()
        self._setup_loai_ban_combo()
        self._wire_signals()
        self._apply_permissions()
        self._setup_session_status()
        self.refresh_loai_ban()
        self.refresh_ban()
        self.refresh_nhan_vien()
        self.refresh_chuc_vu()
        self.refresh_ca_lam()
        self._setup_luong_dates()
        self.refresh_cham_cong()
        self.refresh_bang_luong()
        self.refresh_dich_vu()
        self.refresh_phien_choi_ui()
        self.refresh_hoa_don()
        self._setup_doanh_thu_dates()
        self.refresh_doanh_thu()
        self.refresh_tai_khoan()

    def _tab_index_by_name(self, name: str) -> int:
        tw = self._view.tabWidget
        for i in range(tw.count()):
            w = tw.widget(i)
            if w is not None and w.objectName() == name:
                return i
        return -1

    def _init_tables(self) -> None:
        t = self._view.tableBan
        t.setColumnCount(5)
        t.setHorizontalHeaderLabels(["ID", "Tên bàn", "Loại bàn", "Trạng thái", "Giá/giờ"])
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableNhanVien
        t.setColumnCount(5)
        t.setHorizontalHeaderLabels(["ID", "Họ tên", "SĐT", "Lương/giờ", "Chức vụ"])
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableChucVu
        t.setColumnCount(3)
        t.setHorizontalHeaderLabels(["ID", "Tên", "Hệ số"])
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableCaLam
        t.setColumnCount(5)
        t.setHorizontalHeaderLabels(["ID", "Tên", "Bắt đầu", "Kết thúc", "Hệ số"])
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableChamCong
        t.setColumnCount(8)
        t.setHorizontalHeaderLabels(
            ["ID", "Ngày", "Nhân viên", "Ca", "Bắt đầu", "Kết thúc", "Hệ số ca", "Ghi chú"]
        )
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableBangLuong
        t.setColumnCount(6)
        t.setHorizontalHeaderLabels(["NV", "Chức vụ", "Lương/giờ", "Tổng giờ", "Tổng tiền", "Ghi chú"])
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tablePhienDangChoi
        t.setColumnCount(5)
        t.setHorizontalHeaderLabels(["ID", "Bàn", "Giờ bắt đầu", "Giá/giờ", "Nhân viên"])
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableDichVuTamPhien
        t.setColumnCount(4)
        t.setHorizontalHeaderLabels(["Dịch vụ", "Đơn giá", "SL", "Thành tiền"])
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableDichVu
        t.setColumnCount(3)
        t.setHorizontalHeaderLabels(["ID", "Tên", "Giá"])
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableHoaDon
        t.setColumnCount(8)
        t.setHorizontalHeaderLabels(
            ["ID", "Bàn", "Giờ chơi (h)", "Tiền bàn", "DV", "Tổng", "Ngày tạo", "Phiên"]
        )
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableDoanhThu
        t.setColumnCount(7)
        t.setHorizontalHeaderLabels(
            ["ID", "Bàn", "Giờ chơi (h)", "Tiền bàn", "DV", "Tổng", "Ngày tạo"]
        )
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableTaiKhoan
        t.setColumnCount(5)
        t.setHorizontalHeaderLabels(
            ["ID", "Tên đăng nhập", "Họ tên", "Vai trò", "Ngày tạo"]
        )
        t.horizontalHeader().setStretchLastSection(True)

        t = self._view.tableLoaiBan
        t.setColumnCount(4)
        t.setHorizontalHeaderLabels(["ID", "Tên loại", "Giá mặc định", "Sale (%)"])
        t.horizontalHeader().setStretchLastSection(True)

    def _wire_signals(self) -> None:
        v = self._view
        v.btnBanThem.clicked.connect(self._on_ban_them)
        v.btnBanSua.clicked.connect(self._on_ban_sua)
        v.btnBanXoa.clicked.connect(self._on_ban_xoa)
        v.btnBanLamMoi.clicked.connect(self.refresh_ban)
        v.tableBan.itemSelectionChanged.connect(self._on_ban_select)
        v.comboLoaiBan.currentIndexChanged.connect(self._on_combo_loai_ban_changed)
        v.chkGiaRieng.toggled.connect(self._on_chk_gia_rieng_toggled)
        v.comboLocLoaiBan.currentIndexChanged.connect(
            lambda _i: self._on_filter_loai_changed(v.comboLocLoaiBan)
        )
        v.comboLocPhien.currentIndexChanged.connect(
            lambda _i: self._on_filter_loai_changed(v.comboLocPhien)
        )

        v.btnNVThem.clicked.connect(self._on_nv_them)
        v.btnNVSua.clicked.connect(self._on_nv_sua)
        v.btnNVXoa.clicked.connect(self._on_nv_xoa)
        v.btnNVLamMoi.clicked.connect(self.refresh_nhan_vien)
        v.tableNhanVien.itemSelectionChanged.connect(self._on_nv_select)

        v.btnChucVuLamMoi.clicked.connect(self.refresh_chuc_vu)
        v.btnChucVuThem.clicked.connect(self._on_chuc_vu_them)
        v.btnChucVuSua.clicked.connect(self._on_chuc_vu_sua)
        v.btnChucVuXoa.clicked.connect(self._on_chuc_vu_xoa)
        v.tableChucVu.itemSelectionChanged.connect(self._on_chuc_vu_select)

        v.btnCaLamMoi.clicked.connect(self.refresh_ca_lam)
        v.btnCaThem.clicked.connect(self._on_ca_them)
        v.btnCaSua.clicked.connect(self._on_ca_sua)
        v.btnCaXoa.clicked.connect(self._on_ca_xoa)
        v.tableCaLam.itemSelectionChanged.connect(self._on_ca_select)

        v.btnChamCongThem.clicked.connect(self._on_cham_cong_them)
        v.btnChamCongXoa.clicked.connect(self._on_cham_cong_xoa)
        v.btnTinhLuong.clicked.connect(self._on_tinh_luong)
        v.btnTraLuong.clicked.connect(self._on_tra_luong)

        v.btnBatDauPhien.clicked.connect(self._on_bat_dau_phien)
        v.tablePhienDangChoi.itemSelectionChanged.connect(self._on_phien_select)
        v.btnThemDVPhien.clicked.connect(self._on_them_dv_phien)
        v.btnXoaDongDV.clicked.connect(self._on_xoa_dong_dv)
        v.btnKetThucPhien.clicked.connect(self._on_ket_thuc_phien)

        v.btnDVThem.clicked.connect(self._on_dv_them)
        v.btnDVSua.clicked.connect(self._on_dv_sua)
        v.btnDVXoa.clicked.connect(self._on_dv_xoa)
        v.btnDVLamMoi.clicked.connect(self.refresh_dich_vu)
        v.tableDichVu.itemSelectionChanged.connect(self._on_dv_select)

        v.btnHoaDonLamMoi.clicked.connect(self.refresh_hoa_don)
        v.btnXuatHoaDon.clicked.connect(self._on_xuat_hoa_don)

        v.btnLocDoanhThu.clicked.connect(self.refresh_doanh_thu)

        v.actionTaoTaiKhoan.triggered.connect(self._on_tao_tai_khoan)
        v.actionDangXuat.triggered.connect(self._on_dang_xuat)

        v.btnTaiKhoanLamMoi.clicked.connect(self.refresh_tai_khoan)
        v.btnTaiKhoanThem.clicked.connect(self._on_tao_tai_khoan)
        v.btnTaiKhoanDoiMatKhau.clicked.connect(self._on_tai_khoan_doi_mat_khau)
        v.btnTaiKhoanXoa.clicked.connect(self._on_tai_khoan_xoa)

        v.btnLoaiBanLamMoi.clicked.connect(self.refresh_loai_ban)
        v.btnLoaiBanThem.clicked.connect(self._on_loai_ban_them)
        v.btnLoaiBanSua.clicked.connect(self._on_loai_ban_sua)
        v.btnLoaiBanXoa.clicked.connect(self._on_loai_ban_xoa)
        v.tableLoaiBan.itemSelectionChanged.connect(self._on_loai_ban_select)

    def _setup_doanh_thu_dates(self) -> None:
        today = date.today()
        self._view.dateTu.setDate(today)
        self._view.dateDen.setDate(today)

    def _setup_luong_dates(self) -> None:
        today = date.today()
        self._view.dateCCNgay.setDate(today)
        self._view.dateLuongTu.setDate(today)
        self._view.dateLuongDen.setDate(today)

    def _setup_loai_ban_combo(self) -> None:
        self._reload_combo_loai_ban()
        self._on_chk_gia_rieng_toggled(self._view.chkGiaRieng.isChecked())

    def _reload_combo_loai_ban(self) -> None:
        c = self._view.comboLoaiBan
        c.blockSignals(True)
        c.clear()
        c.addItem("(Chưa gán loại)", None)
        for r in self._loai_ban.list_all():
            c.addItem(r["ten"], int(r["id"]))
        c.setCurrentIndex(0)
        c.blockSignals(False)
        self._update_loai_ban_info_labels()

    def _selected_loai_ban_id_from_combo(self) -> int | None:
        d = self._view.comboLoaiBan.currentData()
        return int(d) if d is not None else None

    def _update_loai_ban_info_labels(self) -> None:
        loai_id = self._selected_loai_ban_id_from_combo()
        if loai_id is None:
            self._view.labelGiaMacDinhValue.setText("(chưa chọn)")
            self._view.labelSalePercentValue.setText("0")
            return
        r = self._loai_ban.get(loai_id)
        if not r:
            self._view.labelGiaMacDinhValue.setText("(chưa chọn)")
            self._view.labelSalePercentValue.setText("0")
            return
        self._view.labelGiaMacDinhValue.setText(f"{_money(float(r['gia_gio_mac_dinh']))} đ/giờ")
        self._view.labelSalePercentValue.setText(f"{float(r['sale_percent']):.0f}")

    def _setup_session_status(self) -> None:
        role = "Quản trị" if self._session.is_admin() else "Nhân viên"
        name = self._session.ho_ten or self._session.ten_dang_nhap
        self._view.statusBar().showMessage(f"Đăng nhập: {name} ({role})", 0)

    def _apply_permissions(self) -> None:
        staff = self._session.vai_tro == "nhan_vien"
        admin = self._session.is_admin()
        tb = self._view.tabWidget.tabBar()
        for name, visible in (
            ("tabNhanVien", not staff),
            ("tabLoaiBan", not staff),
            ("tabTaiKhoan", admin),
            ("tabDoanhThu", not staff),
        ):
            i = self._tab_index_by_name(name)
            if i >= 0:
                tb.setTabVisible(i, visible)
        self._view.btnBanThem.setEnabled(not staff)
        self._view.btnBanSua.setEnabled(not staff)
        self._view.btnBanXoa.setEnabled(not staff)
        self._view.editTenBan.setReadOnly(staff)
        self._view.comboLoaiBan.setEnabled(not staff)
        self._view.spinGiaGio.setReadOnly(staff)
        self._view.chkGiaRieng.setEnabled(not staff)
        self._view.btnNVThem.setEnabled(not staff)
        self._view.btnNVSua.setEnabled(not staff)
        self._view.btnNVXoa.setEnabled(not staff)
        self._view.btnDVThem.setEnabled(not staff)
        self._view.btnDVSua.setEnabled(not staff)
        self._view.btnDVXoa.setEnabled(not staff)
        self._view.btnLocDoanhThu.setEnabled(not staff)
        self._view.actionTaoTaiKhoan.setVisible(admin)
        self._view.actionTaoTaiKhoan.setEnabled(admin)
        for w in (
            self._view.btnTaiKhoanLamMoi,
            self._view.btnTaiKhoanThem,
            self._view.btnTaiKhoanDoiMatKhau,
            self._view.btnTaiKhoanXoa,
        ):
            w.setEnabled(admin)

        for w in (
            self._view.btnLoaiBanLamMoi,
            self._view.btnLoaiBanThem,
            self._view.btnLoaiBanSua,
            self._view.btnLoaiBanXoa,
            self._view.tableLoaiBan,
            self._view.editLoaiBanTen,
            self._view.spinLoaiBanGia,
            self._view.spinLoaiBanSale,
        ):
            w.setEnabled(not staff)

    def _on_tao_tai_khoan(self) -> None:
        if not self._session.is_admin():
            return
        dlg = RegisterDialog(
            self._tai_khoan,
            first_user=False,
            allow_role_select=True,
            parent=self._view,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh_tai_khoan()
            QMessageBox.information(self._view, "Đã tạo", "Đã tạo tài khoản mới.")

    def refresh_tai_khoan(self) -> None:
        if not self._session.is_admin():
            return
        rows = self._tai_khoan.list_all()
        t = self._view.tableTaiKhoan
        role_vn = {"admin": "Quản trị", "nhan_vien": "Nhân viên"}
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ten_dang_nhap"] or ""))
            t.setItem(i, 2, QTableWidgetItem(r["ho_ten"] or ""))
            vr = (r["vai_tro"] or "").strip()
            t.setItem(i, 3, QTableWidgetItem(role_vn.get(vr, vr)))
            t.setItem(i, 4, QTableWidgetItem(str(r["ngay_tao"] or "")))
        t.clearSelection()

    def _selected_tai_khoan_id(self) -> int | None:
        rows = self._view.tableTaiKhoan.selectionModel().selectedRows()
        if not rows:
            return None
        it = self._view.tableTaiKhoan.item(rows[0].row(), 0)
        return int(it.text()) if it else None

    def _on_tai_khoan_doi_mat_khau(self) -> None:
        if not self._session.is_admin():
            return
        uid = self._selected_tai_khoan_id()
        if uid is None:
            QMessageBox.information(
                self._view, "Chọn tài khoản", "Chọn một dòng trong bảng."
            )
            return
        row = self._tai_khoan.get_by_id(uid)
        if not row:
            self.refresh_tai_khoan()
            return
        dlg = ChangePasswordDialog(row["ten_dang_nhap"], parent=self._view)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self._tai_khoan.set_password(uid, dlg.password())
        except ValueError as e:
            QMessageBox.warning(self._view, "Mật khẩu", str(e))
            return
        QMessageBox.information(self._view, "Đã xong", "Đã đổi mật khẩu.")

    def _on_tai_khoan_xoa(self) -> None:
        if not self._session.is_admin():
            return
        uid = self._selected_tai_khoan_id()
        if uid is None:
            QMessageBox.information(
                self._view, "Chọn tài khoản", "Chọn một dòng trong bảng."
            )
            return
        if uid == self._session.user_id:
            QMessageBox.warning(
                self._view, "Không xóa được", "Không thể xóa tài khoản đang đăng nhập."
            )
            return
        row = self._tai_khoan.get_by_id(uid)
        if not row:
            self.refresh_tai_khoan()
            return
        if row["vai_tro"] == "admin" and self._tai_khoan.count_admins() <= 1:
            QMessageBox.warning(
                self._view,
                "Không xóa được",
                "Phải còn ít nhất một tài khoản quản trị.",
            )
            return
        if (
            QMessageBox.question(
                self._view,
                "Xác nhận",
                f"Xóa tài khoản «{row['ten_dang_nhap']}»?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            self._tai_khoan.delete(uid)
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_tai_khoan()

    def _on_dang_xuat(self) -> None:
        if (
            QMessageBox.question(
                self._view,
                "Đăng xuất",
                "Bạn có chắc muốn đăng xuất?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        if self._on_logout:
            self._on_logout()

    @staticmethod
    def _loai_ban_display(r: sqlite3.Row) -> str:
        v = r["loai_ban"]
        return (v or "").strip()

    def _data_to_filter(self, d: object) -> str | None:
        if d is None:
            return None
        if isinstance(d, str):
            return d
        return str(d)

    def _validate_filter_loai(self, distinct: list[str], has_empty: bool) -> None:
        if self._filter_loai is None:
            return
        if self._filter_loai == "":
            if not has_empty:
                self._filter_loai = None
            return
        if self._filter_loai not in distinct:
            self._filter_loai = None

    def _filter_loai_combo_index(self, combo: QComboBox) -> int:
        for i in range(combo.count()):
            d = combo.itemData(i)
            if self._filter_loai is None and d is None:
                return i
            if self._filter_loai is not None and d == self._filter_loai:
                return i
        return 0

    def _populate_filter_loai_combos(self) -> None:
        distinct = self._ban.distinct_loai_ban()
        has_empty = self._ban.has_any_empty_loai()
        self._validate_filter_loai(distinct, has_empty)
        for c in (self._view.comboLocLoaiBan, self._view.comboLocPhien):
            c.blockSignals(True)
            c.clear()
            c.addItem("Tất cả", None)
            if has_empty:
                c.addItem("(Chưa gán loại)", "")
            for lo in distinct:
                c.addItem(lo, lo)
            idx = self._filter_loai_combo_index(c)
            c.setCurrentIndex(idx)
            c.blockSignals(False)
        self._filter_loai = self._data_to_filter(self._view.comboLocLoaiBan.currentData())

    def _on_filter_loai_changed(self, src: QComboBox) -> None:
        if src is self._view.comboLocLoaiBan:
            other = self._view.comboLocPhien
        else:
            other = self._view.comboLocLoaiBan
        other.blockSignals(True)
        other.setCurrentIndex(src.currentIndex())
        other.blockSignals(False)
        self._filter_loai = self._data_to_filter(src.currentData())
        self._refresh_ban_table()
        self._rebuild_phien_ban_tiles()

    def _refresh_ban_table(self) -> None:
        rows = self._ban.list_all(self._filter_loai)
        t = self._view.tableBan
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ten_ban"]))
            t.setItem(i, 2, QTableWidgetItem(self._loai_ban_display(r)))
            tt = "Đang chơi" if r["trang_thai"] == "dang_choi" else "Trống"
            t.setItem(i, 3, QTableWidgetItem(tt))
            t.setItem(i, 4, QTableWidgetItem(_money(float(r["gia_gio"]))))

    # --- Bàn ---
    def refresh_ban(self) -> None:
        self._reload_combo_loai_ban()
        self._populate_filter_loai_combos()
        self._refresh_ban_table()
        self._view.tableBan.clearSelection()
        self._view.editTenBan.clear()
        self._view.comboLoaiBan.setCurrentIndex(0)
        self._view.chkGiaRieng.setChecked(False)
        self._view.spinGiaGio.setValue(50_000)
        self._update_loai_ban_info_labels()

    # --- Loại bàn ---
    def refresh_loai_ban(self) -> None:
        rows = self._loai_ban.list_all()
        t = self._view.tableLoaiBan
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ten"] or ""))
            t.setItem(i, 2, QTableWidgetItem(_money(float(r["gia_gio_mac_dinh"] or 0))))
            t.setItem(i, 3, QTableWidgetItem(f"{float(r['sale_percent'] or 0):.0f}"))
        t.clearSelection()
        self._view.editLoaiBanTen.clear()
        self._view.spinLoaiBanGia.setValue(0)
        self._view.spinLoaiBanSale.setValue(0)
        # refresh combo + filters since type list may change
        self._reload_combo_loai_ban()
        self._populate_filter_loai_combos()

    def _selected_loai_ban_table_id(self) -> int | None:
        rows = self._view.tableLoaiBan.selectionModel().selectedRows()
        if not rows:
            return None
        it = self._view.tableLoaiBan.item(rows[0].row(), 0)
        return int(it.text()) if it else None

    def _on_loai_ban_select(self) -> None:
        lid = self._selected_loai_ban_table_id()
        if lid is None:
            return
        r = self._loai_ban.get(lid)
        if not r:
            return
        self._view.editLoaiBanTen.setText(r["ten"] or "")
        self._view.spinLoaiBanGia.setValue(float(r["gia_gio_mac_dinh"] or 0))
        self._view.spinLoaiBanSale.setValue(float(r["sale_percent"] or 0))

    def _on_loai_ban_them(self) -> None:
        ten = self._view.editLoaiBanTen.text().strip()
        try:
            self._loai_ban.create(
                ten,
                self._view.spinLoaiBanGia.value(),
                self._view.spinLoaiBanSale.value(),
            )
        except ValueError as e:
            QMessageBox.warning(self._view, "Loại bàn", str(e))
            return
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_loai_ban()

    def _on_loai_ban_sua(self) -> None:
        lid = self._selected_loai_ban_table_id()
        if lid is None:
            QMessageBox.information(self._view, "Chọn loại", "Chọn một dòng trong bảng.")
            return
        ten = self._view.editLoaiBanTen.text().strip()
        try:
            self._loai_ban.update(
                lid,
                ten,
                self._view.spinLoaiBanGia.value(),
                self._view.spinLoaiBanSale.value(),
            )
        except ValueError as e:
            QMessageBox.warning(self._view, "Loại bàn", str(e))
            return
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_loai_ban()

    def _on_loai_ban_xoa(self) -> None:
        lid = self._selected_loai_ban_table_id()
        if lid is None:
            QMessageBox.information(self._view, "Chọn loại", "Chọn một dòng trong bảng.")
            return
        r = self._loai_ban.get(lid)
        if not r:
            self.refresh_loai_ban()
            return
        if (
            QMessageBox.question(self._view, "Xác nhận", f"Xóa loại bàn «{r['ten']}»?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            self._loai_ban.delete(lid)
        except ValueError as e:
            QMessageBox.warning(self._view, "Loại bàn", str(e))
            return
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_loai_ban()

    def _set_ban_trong_dang_chon(self, ban_id: int | None) -> None:
        self._ban_trong_dang_chon = ban_id
        if ban_id is None:
            self._view.labelBanDaChonValue.setText("(chưa chọn)")
            self._sync_phien_ban_tile_highlight()
            return
        r = self._ban.get(int(ban_id))
        if not r:
            self._view.labelBanDaChonValue.setText("(chưa chọn)")
            self._ban_trong_dang_chon = None
            self._sync_phien_ban_tile_highlight()
            return
        loai = self._loai_ban_display(r)
        label = f"{r['ten_ban']}"
        if loai:
            label = f"{label} ({loai})"
        self._view.labelBanDaChonValue.setText(f"{label} — {_money(float(r['gia_gio']))}đ/giờ (ID {r['id']})")
        self._sync_phien_ban_tile_highlight()

    def _selected_ban_id(self) -> int | None:
        rows = self._view.tableBan.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        it = self._view.tableBan.item(row, 0)
        return int(it.text()) if it else None

    def _on_ban_select(self) -> None:
        bid = self._selected_ban_id()
        if bid is None:
            return
        r = self._ban.get(bid)
        if not r:
            return
        self._view.editTenBan.setText(r["ten_ban"])
        # Loại bàn theo ID (nếu có)
        loai_id = r["loai_ban_id"]
        if loai_id is None:
            self._view.comboLoaiBan.setCurrentIndex(0)
        else:
            for i in range(self._view.comboLoaiBan.count()):
                if self._view.comboLoaiBan.itemData(i) == int(loai_id):
                    self._view.comboLoaiBan.setCurrentIndex(i)
                    break
        gia_rieng = r["gia_gio_rieng"]
        self._view.chkGiaRieng.setChecked(gia_rieng is not None)
        if gia_rieng is not None:
            self._view.spinGiaGio.setValue(float(gia_rieng))
        else:
            # Hiển thị giá legacy để người dùng dễ nhập nếu muốn override
            self._view.spinGiaGio.setValue(float(r["gia_gio_legacy"]))
        self._update_loai_ban_info_labels()

    def _on_ban_them(self) -> None:
        ten = self._view.editTenBan.text().strip()
        if not ten:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Nhập tên bàn.")
            return
        loai_id = self._selected_loai_ban_id_from_combo()
        gia_rieng = self._view.spinGiaGio.value() if self._view.chkGiaRieng.isChecked() else None
        loai_text = self._view.comboLoaiBan.currentText().strip() if loai_id is not None else ""
        # Legacy fallback: vẫn lưu ban.gia_gio để tương thích dữ liệu cũ
        gia_luu = float(gia_rieng) if gia_rieng is not None else self._view.spinGiaGio.value()
        if loai_id is not None and gia_rieng is None:
            row = self._loai_ban.get(loai_id)
            if row and float(row["gia_gio_mac_dinh"]) > 0:
                gia_luu = float(row["gia_gio_mac_dinh"])
        try:
            self._ban.create(
                ten,
                gia_luu,
                loai_text,
                loai_ban_id=loai_id,
                gia_gio_rieng=gia_rieng,
            )
        except ValueError as e:
            QMessageBox.warning(self._view, "Trùng tên", str(e))
            return
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_ban()
        self.refresh_phien_choi_ui()

    def _on_ban_sua(self) -> None:
        bid = self._selected_ban_id()
        if bid is None:
            QMessageBox.information(self._view, "Chọn bàn", "Chọn một dòng trong bảng.")
            return
        ten = self._view.editTenBan.text().strip()
        if not ten:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Nhập tên bàn.")
            return
        loai_id = self._selected_loai_ban_id_from_combo()
        gia_rieng = self._view.spinGiaGio.value() if self._view.chkGiaRieng.isChecked() else None
        loai_text = self._view.comboLoaiBan.currentText().strip() if loai_id is not None else ""
        gia_luu = float(gia_rieng) if gia_rieng is not None else self._view.spinGiaGio.value()
        if loai_id is not None and gia_rieng is None:
            row = self._loai_ban.get(loai_id)
            if row and float(row["gia_gio_mac_dinh"]) > 0:
                gia_luu = float(row["gia_gio_mac_dinh"])
        try:
            self._ban.update(
                bid,
                ten,
                gia_luu,
                loai_text,
                loai_ban_id=loai_id,
                gia_gio_rieng=gia_rieng,
            )
        except ValueError as e:
            QMessageBox.warning(self._view, "Trùng tên", str(e))
            return
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_ban()
        self.refresh_phien_choi_ui()

    def _on_combo_loai_ban_changed(self, _index: int) -> None:
        self._update_loai_ban_info_labels()

    def _on_chk_gia_rieng_toggled(self, checked: bool) -> None:
        self._view.spinGiaGio.setEnabled(checked and not self._view.spinGiaGio.isReadOnly())

    def _on_ban_xoa(self) -> None:
        bid = self._selected_ban_id()
        if bid is None:
            QMessageBox.information(self._view, "Chọn bàn", "Chọn một dòng trong bảng.")
            return
        r = self._ban.get(bid)
        if r and r["trang_thai"] == "dang_choi":
            QMessageBox.warning(
                self._view, "Không xóa được", "Bàn đang có phiên chơi."
            )
            return
        if QMessageBox.question(self._view, "Xác nhận", "Xóa bàn này?") != QMessageBox.StandardButton.Yes:
            return
        try:
            self._ban.delete(bid)
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_ban()
        self.refresh_phien_choi_ui()

    # --- Nhân viên ---
    def refresh_nhan_vien(self) -> None:
        rows = self._nv.list_all()
        t = self._view.tableNhanVien
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ten"] or ""))
            t.setItem(i, 2, QTableWidgetItem(r["so_dien_thoai"] or ""))
            luong_gio = r["luong_gio"]
            t.setItem(
                i,
                3,
                QTableWidgetItem(_money(float(luong_gio)) if luong_gio is not None else ""),
            )
            t.setItem(i, 4, QTableWidgetItem(r["chuc_vu"] or ""))
        self._fill_combo_nv()
        self._reload_combo_nv_chuc_vu()
        t.clearSelection()
        self._view.editNVTen.clear()
        self._view.editNVSDT.clear()
        self._view.spinNVLuong.setValue(0)
        self._view.comboNVChucVu.setCurrentIndex(0)

    def _fill_combo_nv(self) -> None:
        c = self._view.comboNVPhien
        c.clear()
        c.addItem("(Không chọn)", None)
        for r in self._nv.list_all():
            c.addItem(r["ten"], r["id"])

        c2 = self._view.comboCCNhanVien
        c2.clear()
        for r in self._nv.list_all():
            c2.addItem(r["ten"], r["id"])

    def _reload_combo_nv_chuc_vu(self) -> None:
        c = self._view.comboNVChucVu
        c.blockSignals(True)
        c.clear()
        c.addItem("(Không chọn)", None)
        for r in self._chuc_vu.list_all():
            c.addItem(r["ten"], int(r["id"]))
        c.setCurrentIndex(0)
        c.blockSignals(False)

    def _selected_nv_table_id(self) -> int | None:
        rows = self._view.tableNhanVien.selectionModel().selectedRows()
        if not rows:
            return None
        it = self._view.tableNhanVien.item(rows[0].row(), 0)
        return int(it.text()) if it else None

    def _on_nv_select(self) -> None:
        nid = self._selected_nv_table_id()
        if nid is None:
            return
        r = self._nv.get(nid)
        if not r:
            return
        self._view.editNVTen.setText(r["ten"] or "")
        self._view.editNVSDT.setText(r["so_dien_thoai"] or "")
        self._view.spinNVLuong.setValue(float(r["luong_gio"] or 0))
        cv_id = r["chuc_vu_id"]
        idx = self._view.comboNVChucVu.findData(int(cv_id)) if cv_id is not None else 0
        self._view.comboNVChucVu.setCurrentIndex(idx if idx >= 0 else 0)

    def _on_nv_them(self) -> None:
        ten = self._view.editNVTen.text().strip()
        if not ten:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Nhập họ tên.")
            return
        luong_gio = self._view.spinNVLuong.value()
        cv_id = self._view.comboNVChucVu.currentData()
        self._nv.create(
            ten,
            self._view.editNVSDT.text().strip() or None,
            luong_gio if luong_gio > 0 else None,
            int(cv_id) if cv_id is not None else None,
        )
        self.refresh_nhan_vien()

    def _on_nv_sua(self) -> None:
        nid = self._selected_nv_table_id()
        if nid is None:
            QMessageBox.information(self._view, "Chọn NV", "Chọn một dòng trong bảng.")
            return
        ten = self._view.editNVTen.text().strip()
        if not ten:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Nhập họ tên.")
            return
        luong_gio = self._view.spinNVLuong.value()
        cv_id = self._view.comboNVChucVu.currentData()
        self._nv.update(
            nid,
            ten,
            self._view.editNVSDT.text().strip() or None,
            luong_gio if luong_gio > 0 else None,
            int(cv_id) if cv_id is not None else None,
        )
        self.refresh_nhan_vien()

    # --- Chức vụ ---
    def refresh_chuc_vu(self) -> None:
        rows = self._chuc_vu.list_all()
        t = self._view.tableChucVu
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ten"]))
            t.setItem(i, 2, QTableWidgetItem(f"{float(r['he_so']):.2f}"))
        t.clearSelection()
        self._view.editChucVuTen.clear()
        self._view.spinChucVuHeSo.setValue(1.0)
        self._reload_combo_nv_chuc_vu()

    def _selected_chuc_vu_id(self) -> int | None:
        rows = self._view.tableChucVu.selectionModel().selectedRows()
        if not rows:
            return None
        it = self._view.tableChucVu.item(rows[0].row(), 0)
        return int(it.text()) if it else None

    def _on_chuc_vu_select(self) -> None:
        cv_id = self._selected_chuc_vu_id()
        if cv_id is None:
            return
        r = self._chuc_vu.get(cv_id)
        if not r:
            return
        self._view.editChucVuTen.setText(r["ten"])
        self._view.spinChucVuHeSo.setValue(float(r["he_so"]))

    def _on_chuc_vu_them(self) -> None:
        ten = self._view.editChucVuTen.text().strip()
        if not ten:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Nhập tên chức vụ.")
            return
        try:
            self._chuc_vu.create(ten, self._view.spinChucVuHeSo.value())
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_chuc_vu()

    def _on_chuc_vu_sua(self) -> None:
        cv_id = self._selected_chuc_vu_id()
        if cv_id is None:
            QMessageBox.information(self._view, "Chọn chức vụ", "Chọn một dòng trong bảng.")
            return
        ten = self._view.editChucVuTen.text().strip()
        if not ten:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Nhập tên chức vụ.")
            return
        try:
            self._chuc_vu.update(cv_id, ten, self._view.spinChucVuHeSo.value())
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_chuc_vu()

    def _on_chuc_vu_xoa(self) -> None:
        cv_id = self._selected_chuc_vu_id()
        if cv_id is None:
            QMessageBox.information(self._view, "Chọn chức vụ", "Chọn một dòng trong bảng.")
            return
        if QMessageBox.question(self._view, "Xác nhận", "Xóa chức vụ này?") != QMessageBox.StandardButton.Yes:
            return
        try:
            self._chuc_vu.delete(cv_id)
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_chuc_vu()

    # --- Ca làm ---
    def refresh_ca_lam(self) -> None:
        rows = self._ca_lam.list_all()
        t = self._view.tableCaLam
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ten"]))
            t.setItem(i, 2, QTableWidgetItem(r["gio_bat_dau"]))
            t.setItem(i, 3, QTableWidgetItem(r["gio_ket_thuc"]))
            t.setItem(i, 4, QTableWidgetItem(f"{float(r['he_so']):.2f}"))
        t.clearSelection()
        self._view.editCaTen.clear()
        self._view.editCaBatDau.clear()
        self._view.editCaKetThuc.clear()
        self._view.spinCaHeSo.setValue(1.0)
        self._reload_combo_cc_ca()

    def _reload_combo_cc_ca(self) -> None:
        c = self._view.comboCCCa
        c.clear()
        for r in self._ca_lam.list_all():
            c.addItem(f"{r['ten']} (x{float(r['he_so']):.2f})", int(r["id"]))

    def _selected_ca_id(self) -> int | None:
        rows = self._view.tableCaLam.selectionModel().selectedRows()
        if not rows:
            return None
        it = self._view.tableCaLam.item(rows[0].row(), 0)
        return int(it.text()) if it else None

    def _on_ca_select(self) -> None:
        ca_id = self._selected_ca_id()
        if ca_id is None:
            return
        r = self._ca_lam.get(ca_id)
        if not r:
            return
        self._view.editCaTen.setText(r["ten"])
        self._view.editCaBatDau.setText(r["gio_bat_dau"])
        self._view.editCaKetThuc.setText(r["gio_ket_thuc"])
        self._view.spinCaHeSo.setValue(float(r["he_so"]))

    def _on_ca_them(self) -> None:
        ten = self._view.editCaTen.text().strip()
        bd = self._view.editCaBatDau.text().strip()
        kt = self._view.editCaKetThuc.text().strip()
        if not ten or not bd or not kt:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Nhập tên ca và giờ bắt đầu/kết thúc (HH:MM).")
            return
        try:
            self._ca_lam.create(ten, bd, kt, self._view.spinCaHeSo.value())
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_ca_lam()

    def _on_ca_sua(self) -> None:
        ca_id = self._selected_ca_id()
        if ca_id is None:
            QMessageBox.information(self._view, "Chọn ca", "Chọn một dòng trong bảng.")
            return
        ten = self._view.editCaTen.text().strip()
        bd = self._view.editCaBatDau.text().strip()
        kt = self._view.editCaKetThuc.text().strip()
        if not ten or not bd or not kt:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Nhập tên ca và giờ bắt đầu/kết thúc (HH:MM).")
            return
        try:
            self._ca_lam.update(ca_id, ten, bd, kt, self._view.spinCaHeSo.value())
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_ca_lam()

    def _on_ca_xoa(self) -> None:
        ca_id = self._selected_ca_id()
        if ca_id is None:
            QMessageBox.information(self._view, "Chọn ca", "Chọn một dòng trong bảng.")
            return
        if QMessageBox.question(self._view, "Xác nhận", "Xóa ca này?") != QMessageBox.StandardButton.Yes:
            return
        try:
            self._ca_lam.delete(ca_id)
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_ca_lam()

    # --- Chấm công & lương ---
    def refresh_cham_cong(self) -> None:
        tu = self._view.dateLuongTu.date().toString("yyyy-MM-dd")
        den = self._view.dateLuongDen.date().toString("yyyy-MM-dd")
        rows = self._phan_cong.list_by_date_range(tu, den)
        t = self._view.tableChamCong
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(str(r["ngay"])))
            t.setItem(i, 2, QTableWidgetItem(str(r["nhan_vien_ten"])))
            t.setItem(i, 3, QTableWidgetItem(str(r["ca_ten"])))
            t.setItem(i, 4, QTableWidgetItem(str(r["gio_bat_dau"])))
            t.setItem(i, 5, QTableWidgetItem(str(r["gio_ket_thuc"])))
            t.setItem(i, 6, QTableWidgetItem(f"{float(r['ca_he_so'] or 1.0):.2f}"))
            t.setItem(i, 7, QTableWidgetItem(str(r["ghi_chu"] or "")))

    def refresh_bang_luong(self) -> None:
        self._view.tableBangLuong.setRowCount(0)
        self._view.labelTongLuong.setText("Tổng: 0 VNĐ")

    def _selected_cham_cong_id(self) -> int | None:
        rows = self._view.tableChamCong.selectionModel().selectedRows()
        if not rows:
            return None
        it = self._view.tableChamCong.item(rows[0].row(), 0)
        return int(it.text()) if it else None

    def _on_cham_cong_them(self) -> None:
        nv_id = self._view.comboCCNhanVien.currentData()
        ca_id = self._view.comboCCCa.currentData()
        if nv_id is None or ca_id is None:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Chọn nhân viên và ca.")
            return
        ngay = self._view.dateCCNgay.date().toString("yyyy-MM-dd")
        try:
            # Phân ca: click thêm 1 ca; tăng ca = thêm nhiều dòng (cùng ngày, thêm ca khác)
            self._phan_cong.create(int(nv_id), int(ca_id), ngay)
        except Exception as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_cham_cong()

    def _on_cham_cong_xoa(self) -> None:
        cc_id = self._selected_cham_cong_id()
        if cc_id is None:
            QMessageBox.information(self._view, "Chọn dòng", "Chọn một dòng phân công để xóa.")
            return
        if QMessageBox.question(self._view, "Xác nhận", "Xóa phân công ca này?") != QMessageBox.StandardButton.Yes:
            return
        self._phan_cong.delete(cc_id)
        self.refresh_cham_cong()

    def _on_tinh_luong(self) -> None:
        from datetime import date as _date
        from app.models.bang_luong_model import ky_luong_15

        tu_d, den_d = ky_luong_15(_date.today())
        tu = tu_d.isoformat()
        den = den_d.isoformat()
        self._view.dateLuongTu.setDate(tu_d)
        self._view.dateLuongDen.setDate(den_d)
        rows = self._bang_luong.tinh_bang_luong_tu_phan_cong(tu, den)
        t = self._view.tableBangLuong
        t.setRowCount(len(rows))
        tong = 0.0
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(r.ten))
            t.setItem(i, 1, QTableWidgetItem(r.chuc_vu))
            t.setItem(i, 2, QTableWidgetItem(_money(r.luong_gio)))
            t.setItem(i, 3, QTableWidgetItem(f"{r.tong_gio:.2f}"))
            t.setItem(i, 4, QTableWidgetItem(_money(r.tong_tien)))
            t.setItem(i, 5, QTableWidgetItem(f"Kỳ 15: {tu} → {den}"))
            tong += r.tong_tien
        self._view.labelTongLuong.setText(f"Tổng: {_money(tong)} VNĐ")

    def _on_tra_luong(self) -> None:
        from datetime import date as _date
        from app.models.bang_luong_model import ky_luong_15

        tu_d, den_d = ky_luong_15(_date.today())
        tu = tu_d.isoformat()
        den = den_d.isoformat()
        rows = self._bang_luong.tinh_bang_luong_tu_phan_cong(tu, den)
        if not rows:
            QMessageBox.information(self._view, "Không có dữ liệu", "Kỳ này chưa có phân công ca.")
            return
        try:
            n = self._bang_luong.chot_va_tra_luong(tu, den, rows, ghi_chu="Trả lương kỳ 15")
        except ValueError as e:
            QMessageBox.warning(self._view, "Không thể trả lương", str(e))
            return
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        QMessageBox.information(
            self._view, "Đã trả lương", f"Đã chốt & trả lương kỳ {tu} → {den} cho {n} nhân viên."
        )

    def _on_nv_xoa(self) -> None:
        nid = self._selected_nv_table_id()
        if nid is None:
            QMessageBox.information(self._view, "Chọn NV", "Chọn một dòng trong bảng.")
            return
        if QMessageBox.question(self._view, "Xác nhận", "Xóa nhân viên này?") != QMessageBox.StandardButton.Yes:
            return
        try:
            self._nv.delete(nid)
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_nhan_vien()

    # --- Dịch vụ (danh mục) ---
    def refresh_dich_vu(self) -> None:
        rows = self._dv.list_all()
        t = self._view.tableDichVu
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ten"]))
            t.setItem(i, 2, QTableWidgetItem(_money(float(r["gia"]))))
        self._fill_combo_dv_phien()
        t.clearSelection()
        self._view.editDVTen.clear()
        self._view.spinDVGia.setValue(0)

    def _fill_combo_dv_phien(self) -> None:
        c = self._view.comboDichVuPhien
        c.clear()
        for r in self._dv.list_all():
            c.addItem(f"{r['ten']} — {_money(float(r['gia']))}đ", r["id"])

    def _selected_dv_id(self) -> int | None:
        rows = self._view.tableDichVu.selectionModel().selectedRows()
        if not rows:
            return None
        it = self._view.tableDichVu.item(rows[0].row(), 0)
        return int(it.text()) if it else None

    def _on_dv_select(self) -> None:
        did = self._selected_dv_id()
        if did is None:
            return
        r = self._dv.get(did)
        if not r:
            return
        self._view.editDVTen.setText(r["ten"])
        self._view.spinDVGia.setValue(float(r["gia"]))

    def _on_dv_them(self) -> None:
        ten = self._view.editDVTen.text().strip()
        if not ten:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Nhập tên dịch vụ.")
            return
        self._dv.create(ten, self._view.spinDVGia.value())
        self.refresh_dich_vu()

    def _on_dv_sua(self) -> None:
        did = self._selected_dv_id()
        if did is None:
            QMessageBox.information(self._view, "Chọn DV", "Chọn một dòng trong bảng.")
            return
        ten = self._view.editDVTen.text().strip()
        if not ten:
            QMessageBox.warning(self._view, "Thiếu dữ liệu", "Nhập tên dịch vụ.")
            return
        self._dv.update(did, ten, self._view.spinDVGia.value())
        self.refresh_dich_vu()

    def _on_dv_xoa(self) -> None:
        did = self._selected_dv_id()
        if did is None:
            QMessageBox.information(self._view, "Chọn DV", "Chọn một dòng trong bảng.")
            return
        if QMessageBox.question(self._view, "Xác nhận", "Xóa dịch vụ này?") != QMessageBox.StandardButton.Yes:
            return
        try:
            self._dv.delete(did)
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self.refresh_dich_vu()

    # --- Phiên chơi ---
    def _rebuild_phien_ban_tiles(self) -> None:
        grid = self._view.gridLayoutPhienBanTiles
        while (item := grid.takeAt(0)) is not None:
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._phien_ban_tiles.clear()

        rows = self._ban.list_all(self._filter_loai)
        cols = 4
        for i, r in enumerate(rows):
            ban_id = int(r["id"])
            trong = r["trang_thai"] != "dang_choi"
            tile = BanTile(
                ban_id,
                r["ten_ban"],
                trong,
                _money(float(r["gia_gio"])),
                self._loai_ban_display(r),
            )
            tile.clicked.connect(self._on_phien_ban_tile_clicked)
            row, col = divmod(i, cols)
            grid.addWidget(tile, row, col)
            self._phien_ban_tiles[ban_id] = tile
        for c in range(cols):
            grid.setColumnStretch(c, 1)
        self._sync_phien_ban_tile_highlight()

    def _sync_phien_ban_tile_highlight(self) -> None:
        highlight: int | None = None
        pid = self._selected_phien_id()
        if pid is not None:
            row = self._phien.get(pid)
            if row:
                highlight = int(row["ban_id"])
        if highlight is None:
            if self._ban_trong_dang_chon is not None:
                highlight = int(self._ban_trong_dang_chon)
        for bid, w in self._phien_ban_tiles.items():
            w.set_selected(bid == highlight)

    def _on_phien_ban_tile_clicked(self, ban_id: int) -> None:
        r = self._ban.get(ban_id)
        if not r:
            return
        if r["trang_thai"] == "dang_choi":
            for row in self._phien.list_active():
                if int(row["ban_id"]) == ban_id:
                    self._select_phien_row(int(row["id"]))
                    return
        # Bàn trống → chọn để bắt đầu phiên (không dùng combobox).
        self._view.tablePhienDangChoi.clearSelection()
        self._set_ban_trong_dang_chon(ban_id)

    def refresh_phien_choi_ui(self) -> None:
        self._fill_combo_nv()
        rows = self._phien.list_active()
        t = self._view.tablePhienDangChoi
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ten_ban"]))
            t.setItem(i, 2, QTableWidgetItem(str(r["gio_bat_dau"])))
            gia_ap = r["gia_gio_ap_dung"] if r["gia_gio_ap_dung"] is not None else r["gia_gio"]
            t.setItem(i, 3, QTableWidgetItem(_money(float(gia_ap))))
            nv = ""
            if r["nhan_vien_id"]:
                n = self._nv.get(int(r["nhan_vien_id"]))
                nv = n["ten"] if n else str(r["nhan_vien_id"])
            t.setItem(i, 4, QTableWidgetItem(nv))
        for pid in list(self._tam_dich_vu_theo_phien.keys()):
            if not any(int(r["id"]) == pid for r in rows):
                del self._tam_dich_vu_theo_phien[pid]
        if self._phien_dang_chon is not None and not any(
            int(r["id"]) == self._phien_dang_chon for r in rows
        ):
            self._phien_dang_chon = None
        self._render_tam_dich_vu_table()
        self._rebuild_phien_ban_tiles()
        # Nếu bàn đã chọn không còn trống, bỏ chọn.
        if self._ban_trong_dang_chon is not None:
            r = self._ban.get(int(self._ban_trong_dang_chon))
            if not r or r["trang_thai"] == "dang_choi":
                self._set_ban_trong_dang_chon(None)

    def _selected_phien_id(self) -> int | None:
        rows = self._view.tablePhienDangChoi.selectionModel().selectedRows()
        if not rows:
            return None
        it = self._view.tablePhienDangChoi.item(rows[0].row(), 0)
        return int(it.text()) if it else None

    def _on_phien_select(self) -> None:
        self._phien_dang_chon = self._selected_phien_id()
        self._render_tam_dich_vu_table()
        self._sync_phien_ban_tile_highlight()

    def _on_bat_dau_phien(self) -> None:
        ban_id = self._ban_trong_dang_chon
        if ban_id is None:
            QMessageBox.information(
                self._view,
                "Chọn bàn",
                "Bấm chọn một bàn trống trên sơ đồ để bắt đầu phiên.",
            )
            return
        r = self._ban.get(int(ban_id))
        if not r:
            self._set_ban_trong_dang_chon(None)
            return
        if r["trang_thai"] == "dang_choi":
            QMessageBox.warning(self._view, "Bàn đang chơi", "Bàn này đang có phiên chơi.")
            self._set_ban_trong_dang_chon(None)
            return
        nv_id = self._view.comboNVPhien.currentData()
        gia_ap = float(r["gia_gio"])
        sale_ap = float(r["sale_percent"] or 0)
        try:
            pid = self._phien.create(
                int(ban_id),
                int(nv_id) if nv_id is not None else None,
                gia_ap,
                sale_ap,
            )
            self._ban.set_trang_thai(int(ban_id), "dang_choi")
            self._tam_dich_vu_theo_phien[pid] = []
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self._set_ban_trong_dang_chon(None)
        self.refresh_ban()
        self.refresh_phien_choi_ui()
        self._select_phien_row(pid)

    def _select_phien_row(self, phien_id: int) -> None:
        t = self._view.tablePhienDangChoi
        for row in range(t.rowCount()):
            it = t.item(row, 0)
            if it and int(it.text()) == phien_id:
                t.selectRow(row)
                self._phien_dang_chon = phien_id
                return

    def _current_phien_for_dv(self) -> int | None:
        pid = self._selected_phien_id()
        if pid is not None:
            return pid
        return self._phien_dang_chon

    def _on_them_dv_phien(self) -> None:
        pid = self._current_phien_for_dv()
        if pid is None:
            QMessageBox.information(self._view, "Chọn phiên", "Chọn phiên đang chơi trong bảng.")
            return
        c = self._view.comboDichVuPhien
        if c.currentIndex() < 0:
            return
        dv_id = int(c.currentData())
        r = self._dv.get(dv_id)
        if not r:
            return
        sl = self._view.spinSoLuongDV.value()
        lst = self._tam_dich_vu_theo_phien.setdefault(pid, [])
        lst.append(_TamDichVu(dv_id, r["ten"], float(r["gia"]), sl))
        self._render_tam_dich_vu_table()

    def _on_xoa_dong_dv(self) -> None:
        pid = self._current_phien_for_dv()
        if pid is None:
            return
        t = self._view.tableDichVuTamPhien
        rows = t.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self._view, "Chọn dòng", "Chọn một dòng dịch vụ để xóa.")
            return
        r = rows[0].row()
        lst = self._tam_dich_vu_theo_phien.get(pid, [])
        if 0 <= r < len(lst):
            lst.pop(r)
        self._render_tam_dich_vu_table()

    def _render_tam_dich_vu_table(self) -> None:
        pid = self._current_phien_for_dv()
        lst = self._tam_dich_vu_theo_phien.get(pid or -1, [])
        t = self._view.tableDichVuTamPhien
        t.setRowCount(len(lst))
        tong = 0.0
        for i, line in enumerate(lst):
            t.setItem(i, 0, QTableWidgetItem(line.ten))
            t.setItem(i, 1, QTableWidgetItem(_money(line.don_gia)))
            t.setItem(i, 2, QTableWidgetItem(str(line.so_luong)))
            t.setItem(i, 3, QTableWidgetItem(_money(line.thanh_tien)))
            tong += line.thanh_tien
        self._view.labelTongTamDV.setText(f"{_money(tong)} VNĐ")

    def _gio_choi(self, gio_bat_dau: str) -> float:
        try:
            start = datetime.fromisoformat(gio_bat_dau)
        except ValueError:
            start = datetime.fromisoformat(gio_bat_dau.replace("Z", "+00:00"))
        delta = datetime.now() - start
        h = max(delta.total_seconds() / 3600.0, 1.0 / 60.0)
        return round(h, 4)

    def _on_ket_thuc_phien(self) -> None:
        pid = self._current_phien_for_dv()
        if pid is None:
            QMessageBox.information(self._view, "Chọn phiên", "Chọn phiên đang chơi.")
            return
        r = self._phien.get(pid)
        if not r:
            return
        hours = self._gio_choi(str(r["gio_bat_dau"]))
        gia_ap = float(r["gia_gio_ap_dung"] if r["gia_gio_ap_dung"] is not None else r["gia_gio"])
        sale_ap = float(r["sale_percent_ap_dung"] or 0)
        tien_ban_goc = hours * gia_ap
        tien_ban = round(tien_ban_goc * (1.0 - sale_ap / 100.0), 0)
        lines = self._tam_dich_vu_theo_phien.get(pid, [])
        tien_dv = sum(x.thanh_tien for x in lines)
        tong = tien_ban + tien_dv
        chi_tiet = [
            ChiTietLine(dich_vu_id=x.dich_vu_id, so_luong=x.so_luong, thanh_tien=x.thanh_tien)
            for x in lines
        ]
        try:
            self._hd.finalize_session_checkout(
                pid,
                int(r["ban_id"]),
                hours,
                tien_ban,
                tien_dv,
                tong,
                chi_tiet,
            )
        except sqlite3.Error as e:
            QMessageBox.critical(self._view, "Lỗi", str(e))
            return
        self._tam_dich_vu_theo_phien.pop(pid, None)
        self._phien_dang_chon = None
        self.refresh_ban()
        self.refresh_phien_choi_ui()
        self.refresh_hoa_don()
        self.refresh_doanh_thu()
        QMessageBox.information(
            self._view,
            "Hoàn tất",
            f"Đã lập hóa đơn.\nGiờ chơi: {hours:.2f} h\nGiá áp dụng: {_money(gia_ap)} đ/giờ\nSale: {sale_ap:.0f}%\nTiền bàn: {_money(tien_ban)} đ\nDịch vụ: {_money(tien_dv)} đ\nTổng: {_money(tong)} đ",
        )

    # --- Hóa đơn ---
    def refresh_hoa_don(self) -> None:
        rows = self._hd.list_all()
        t = self._view.tableHoaDon
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ten_ban"]))
            t.setItem(i, 2, QTableWidgetItem(f"{float(r['thoi_gian_choi']):.2f}"))
            t.setItem(i, 3, QTableWidgetItem(_money(float(r["tien_ban"]))))
            t.setItem(i, 4, QTableWidgetItem(_money(float(r["tien_dich_vu"]))))
            t.setItem(i, 5, QTableWidgetItem(_money(float(r["tong_tien"]))))
            t.setItem(i, 6, QTableWidgetItem(str(r["ngay_tao"])))
            t.setItem(i, 7, QTableWidgetItem(str(r["phien_id"])))

    def _selected_hoa_don_id(self) -> int | None:
        rows = self._view.tableHoaDon.selectionModel().selectedRows()
        if not rows:
            return None
        it = self._view.tableHoaDon.item(rows[0].row(), 0)
        return int(it.text()) if it else None

    def _on_xuat_hoa_don(self) -> None:
        hid = self._selected_hoa_don_id()
        if hid is None:
            QMessageBox.information(self._view, "Chọn HĐ", "Chọn một hóa đơn trong bảng.")
            return
        head, details = self._hd.get_full(hid)
        if not head:
            return
        path, _ = QFileDialog.getSaveFileName(
            self._view,
            "Lưu hóa đơn",
            str(Path.home() / f"hoa_don_{hid}.txt"),
            "Text (*.txt);;All (*)",
        )
        if not path:
            return
        lines = [
            "HÓA ĐƠN QUÁN BI-A",
            f"Số hóa đơn: {head['id']}",
            f"Bàn: {head['ten_ban']}",
            f"Phiên chơi: {head['phien_id']}",
            f"Giờ bắt đầu: {head['gio_bat_dau']}",
            f"Giờ kết thúc: {head['gio_ket_thuc']}",
            f"Thời gian chơi (giờ): {float(head['thoi_gian_choi']):.2f}",
            f"Tiền bàn: {_money(float(head['tien_ban']))} VNĐ",
            f"Tiền dịch vụ: {_money(float(head['tien_dich_vu']))} VNĐ",
            f"TỔNG CỘNG: {_money(float(head['tong_tien']))} VNĐ",
            f"Ngày lập: {head['ngay_tao']}",
            "",
            "Chi tiết dịch vụ:",
        ]
        for d in details:
            sl = int(d["so_luong"])
            tt = float(d["thanh_tien"])
            don_gia = tt / sl if sl > 0 else 0.0
            lines.append(
                f"  - {d['ten_dv']}: SL {sl} x {_money(don_gia)} = {_money(tt)}"
            )
        text = "\n".join(lines)
        Path(path).write_text(text, encoding="utf-8")
        QMessageBox.information(self._view, "Đã xuất", f"Đã lưu:\n{path}")

    # --- Doanh thu ---
    def refresh_doanh_thu(self) -> None:
        tu = self._view.dateTu.date().toString("yyyy-MM-dd")
        den = self._view.dateDen.date().toString("yyyy-MM-dd")
        rows = self._hd.list_by_date_range(tu, den)
        tong = self._hd.tong_doanh_thu_khoang(tu, den)
        self._view.labelTongDoanhThu.setText(f"Tổng doanh thu ({tu} → {den}): {_money(tong)} VNĐ")
        t = self._view.tableDoanhThu
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ten_ban"]))
            t.setItem(i, 2, QTableWidgetItem(f"{float(r['thoi_gian_choi']):.2f}"))
            t.setItem(i, 3, QTableWidgetItem(_money(float(r["tien_ban"]))))
            t.setItem(i, 4, QTableWidgetItem(_money(float(r["tien_dich_vu"]))))
            t.setItem(i, 5, QTableWidgetItem(_money(float(r['tong_tien']))))
            t.setItem(i, 6, QTableWidgetItem(str(r["ngay_tao"])))
