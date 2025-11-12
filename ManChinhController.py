# controller.py
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QTimer, QDateTime, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QMenu, QWidgetAction, QMessageBox, QDialog
from PyQt6 import QtCore
from PyQt6.QtGui import QIcon

import sqlite3
import socket
import threading
import subprocess
import platform
import os

from ConnectDB import get_oracle_connection, get_oracle_test_connection, get_sqlite_log_connection, get_sqlite_pause_print_connection, get_sqlite_printer_connection, get_sqlite_camera_connection
from HienCameraController import CameraViewer
from ChuyenMayInController import MaySelectorWidget
from ChonChungTuController import ChungTuForm
from ChiTietController import show_chi_tiet_dialog
from PrinterClient import PrinterClient
from BaoRachVoForm import BaoRachVoForm

# Suppress non-error modal dialogs: information/warning will be printed instead of shown.
# Keep QMessageBox.critical unchanged so real errors still show.
def _silent_information(parent, title, text, *args, **kwargs):
    try:
        print(f"[INFO] {title}: {text}")
    except Exception:
        pass

def _silent_warning(parent, title, text, *args, **kwargs):
    try:
        print(f"[WARNING] {title}: {text}")
    except Exception:
        pass

# Replace the functions used to show non-critical dialogs
QMessageBox.information = _silent_information
QMessageBox.warning = _silent_warning


class Controller:
    def __init__(self, window):
        self.window = window
        self.ui = window
        #set timer cho đồng hồ và ca
        self.timer_dongho = QTimer()
        self.timer_dongho.timeout.connect(self.cap_nhat_dong_ho)
        self.timer_dongho.start(1000)
        #set timer cho check trang thai may in
        self.timer_check_status = QTimer()
        self.timer_check_status.timeout.connect(self.check_trang_thai_may_in)
        self.timer_check_status.start(1000)

        self.tat_ca_so_lo = []
        #Lưu ID chứng từ cho từng máy in
        self.chung_tu_ids = [None] * 5
        # self.conn_oracle = get_oracle_connection
        self.conn_oracle = get_oracle_connection

        # === VIDEOJET 1530 CONTROL ===
        self.printer_clients = [None] * 5  # index 1-4
        self.printer_ips = [""] * 5
        self.current_machine_check = 1

        # Timer gửi GA/E mỗi 2s
        self.update_bao_timer = QTimer()
        self.update_bao_timer.timeout.connect(self.update_bao_cycle)
        self.update_bao_timer.start(300)

        # Tải IP
        self.load_printer_ips()

        self.setup_them_chung_tu_buttons()
        self.cap_nhat_dong_ho()
        self.cap_nhat_ca()
        self.setup_chuyen_may_buttons()
        self.setup_refresh_buttons()
        self.current_camera_viewer = None
        self.setup_camera_buttons()
        self.setup_chi_tiet_buttons()
        self.setup_sl_thuc_xuat_events()
        self.setup_ma_in_events()
        self.load_mang_xuat_data()
        self.tat_ca_so_lo = self.load_tat_ca_so_lo() 
        self.setup_so_lo_combobox()
        self.setup_bat_in_buttons()
        self.setup_tat_in_buttons()
    #----------------------------------------------------------------------------------
    #Chức năng cập nhật ngày giờ và ca
    def cap_nhat_dong_ho(self):
        current = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
        self.ui.txtDateTime.setText(current)

    def cap_nhat_ca(self):
        current_time = QtCore.QDateTime.currentDateTime().time()
        hour = current_time.hour()

        if (hour >= 6 and hour < 14):
            shift = "CA 1"
        elif (hour >= 14 and hour < 22):
            shift = "CA 2"
        else:
            shift = "CA 3"

        self.ui.LabelShift.setText(shift)
    #------------------------------------------------------------------------------
    #Chức năng check trạng thái máy in
    def check_trang_thai_may_in(self):
        """Tự động kiểm tra và khóa/mở field, button theo trạng thái máy in và đổi màu label."""
        for idx in range(1, 5):
            try:
                status_label = getattr(self.ui, f"txtTrangThai{idx}")
                status_text = status_label.text().strip().upper()

                # === DANH SÁCH CÁC WIDGET ===
                fields = [
                    f"txtMaIn{idx}", f"txtBienSoXe{idx}", f"txtSanPham{idx}",
                    f"txtSLCatLenh{idx}", f"txtSLThucXuat{idx}", f"btnRefresh{idx}"
                ]
                buttons = [
                    f"btnThemChungTu{idx}", f"btnSearchMaIn{idx}",
                    f"btnRefresh{idx}"
                ]

                # ===== TRẠNG THÁI: ĐANG IN =====
                if status_text == "ĐANG IN":
                    # Đổi màu label
                    status_label.setStyleSheet("""
                        QLabel {
                            background: qradialgradient(
                                cx:0.5, cy:0.5, radius:0.9,
                                fx:0.5, fy:0.5,
                                stop:0 #cc0000,
                                stop:0.4 #ff3333,
                                stop:1 #ffe6e6
                            );
                            color: white;
                            font-weight: bold;
                            border-radius: 6px;
                            padding: 4px;
                            border: 1px solid #b30000;
                        }
                    """)

                    # KHÓA TẤT CẢ FIELD
                    for field_name in fields:
                        widget = getattr(self.ui, field_name, None)
                        if widget:
                            if hasattr(widget, "setReadOnly"):
                                widget.setReadOnly(True)
                            if hasattr(widget, "setEnabled"):
                                widget.setEnabled(False)

                    # KHÓA CÁC NÚT CƠ BẢN + btnBatIn
                    for btn_name in buttons + [f"btnBatIn{idx}"]:
                        btn = getattr(self.ui, btn_name, None)
                        if btn:
                            btn.setEnabled(False)

                    # MỞ btnTatIn + btnChuyenMayIn
                    btn_tat_in = getattr(self.ui, f"btnTatIn{idx}", None)
                    btn_chuyen = getattr(self.ui, f"btnChuyenMayIn{idx}", None)
                    if btn_tat_in:
                        btn_tat_in.setEnabled(True)
                    if btn_chuyen:
                        btn_chuyen.setEnabled(True)

                # ===== TRẠNG THÁI: DỪNG IN =====
                elif status_text == "DỪNG IN":
                    # Trả màu mặc định
                    status_label.setStyleSheet("")

                    # MỞ TẤT CẢ FIELD
                    for field_name in fields:
                        widget = getattr(self.ui, field_name, None)
                        if widget:
                            if hasattr(widget, "setReadOnly"):
                                widget.setReadOnly(False)
                            if hasattr(widget, "setEnabled"):
                                widget.setEnabled(True)

                    # MỞ CÁC NÚT CƠ BẢN
                    for btn_name in buttons:
                        btn = getattr(self.ui, btn_name, None)
                        if btn:
                            btn.setEnabled(True)

                    # TẮT btnTatIn + btnChuyenMayIn
                    btn_tat_in = getattr(self.ui, f"btnTatIn{idx}", None)
                    btn_chuyen = getattr(self.ui, f"btnChuyenMayIn{idx}", None)
                    if btn_tat_in:
                        btn_tat_in.setEnabled(False)
                    if btn_chuyen:
                        btn_chuyen.setEnabled(False)

                    # === QUẢN LÝ btnBatIn ===
                    # Khi đang DỪNG IN, luôn cho phép Bật In
                    btn_bat_in = getattr(self.ui, f'btnBatIn{idx}', None)
                    if btn_bat_in:
                        btn_bat_in.setEnabled(True)

            except Exception as e:
                print(f"Lỗi khi kiểm tra trạng thái máy in {idx}: {e}")
    #------------------------------------------------------------------------------
    #Chức năng chuyển máy in
    def setup_chuyen_may_buttons(self):
        buttons = [
            self.ui.btnChuyenMayIn1, self.ui.btnChuyenMayIn2,
            self.ui.btnChuyenMayIn3, self.ui.btnChuyenMayIn4
        ]
        labels = [
            self.ui.txtTrangThai1, self.ui.txtTrangThai2,
            self.ui.txtTrangThai3, self.ui.txtTrangThai4
        ]

        for idx, (btn, lbl) in enumerate(zip(buttons, labels), 1):
            # TRUYỀN btn QUA LAMBDA
            btn.clicked.connect(lambda checked=False, b=btn, i=idx: self.show_menu(b, i))

    def show_menu(self, button, current_idx):
        # 1️⃣ Tạo menu chọn máy đích
        widget = MaySelectorWidget()
        choices = [i for i in range(1, 5) if i != current_idx]

        widget.radioMay1.setText(f"Máy In {choices[0]}")
        widget.radioMay2.setText(f"Máy In {choices[1]}")
        widget.radioMay3.setText(f"Máy In {choices[2]}")

        # 2️⃣ Kiểm tra trạng thái máy đích, nếu ĐANG IN thì disable radio đó
        radios = [widget.radioMay1, widget.radioMay2, widget.radioMay3]
        for radio, idx in zip(radios, choices):
            status_label = getattr(self.ui, f"txtTrangThai{idx}")
            status_text = status_label.text().strip().upper()
            if status_text == "ĐANG IN":
                radio.setEnabled(False)
                radio.setStyleSheet("color: gray; background-color: #f0f0f0; border-radius: 12px;")
            else:
                radio.setEnabled(True)
                radio.setStyleSheet("")

        # 3️⃣ Mở menu tại vị trí nút
        menu = QMenu(self.window)
        action = QWidgetAction(menu)
        action.setDefaultWidget(widget)
        menu.addAction(action)
        menu.setFixedWidth(190)

        button_rect = button.rect()
        pos = button.mapToGlobal(button_rect.topLeft())
        pos.setY(pos.y() - menu.sizeHint().height() + 45)

        screen = self.window.screen().availableGeometry()
        if pos.y() < screen.top():
            pos.setY(screen.top() + 10)
        if current_idx == 4:
            pos.setX(pos.x() + button.width() - menu.width() - 170)
        else:
            pos.setX(pos.x() + button.width())

        menu.exec(pos)

        # 4️⃣ Sau khi chọn (nếu có)
        if widget.selected:
            # --- Kiểm tra máy gốc có dữ liệu không ---
            fields_to_check = [
                f"txtMaIn{current_idx}",
                f"txtBienSoXe{current_idx}",
                f"txtSanPham{current_idx}",
                f"txtSLCatLenh{current_idx}",
                f"txtSLThucXuat{current_idx}",
            ]
            has_data = any(
                getattr(self.ui, f).text().strip() != ""
                for f in fields_to_check
                if hasattr(getattr(self.ui, f), "text")
            )

            # Nếu không có dữ liệu máy gốc → bỏ qua (không chuyển, không thông báo)
            if not has_data:
                return

            # --- Nếu có dữ liệu, thực hiện chuyển ---
            target_idx = int(widget.selected.split()[-1])

            fields = [
                "txtBaoDuTinh", "txtBaoDangIn", "txtBaoDaIn",
                "txtMaIn", "txtBienSoXe", "txtSanPham",
                "txtSLCatLenh", "txtSLThucXuat", "txtSoLo", "txtMangXuat"
            ]

            # Sao chép dữ liệu từ máy gốc sang máy đích
            for field in fields:
                src = getattr(self.ui, f"{field}{current_idx}")
                dest = getattr(self.ui, f"{field}{target_idx}")
                if hasattr(src, "currentText"):  # QComboBox
                    dest.setCurrentText(src.currentText())
                else:
                    dest.setText(src.text())

            # Xóa dữ liệu máy gốc
            self.refresh_field(current_idx)
    #----------------------------------------------------------------------------------
    #Chức năng refresh giao diện máy in
    def setup_refresh_buttons(self):
        buttons = [
            self.ui.btnRefresh1, self.ui.btnRefresh2,
            self.ui.btnRefresh3, self.ui.btnRefresh4
        ]

        for idx, btn in enumerate(buttons, 1):
            btn.clicked.connect(lambda checked=False, i=idx: self.refresh_field(i))

    def refresh_field(self, idx):
        # Reset các label tương ứng theo idx (1,2,3,4)
        # DÙNG .setText() CHO CÁC QLineEdit
        getattr(self.ui, f'txtBaoDuTinh{idx}').setText('0')
        getattr(self.ui, f'txtBaoDangIn{idx}').setText('0')
        getattr(self.ui, f'txtBaoDaIn{idx}').setText('0')
        getattr(self.ui, f'txtMaIn{idx}').setText('')
        getattr(self.ui, f'txtBienSoXe{idx}').setText('')
        getattr(self.ui, f'txtSanPham{idx}').setText('')
        getattr(self.ui, f'txtSLCatLenh{idx}').setText('')
        getattr(self.ui, f'txtSLThucXuat{idx}').setText('')
        self.chung_tu_ids[idx] = None

        # RIÊNG txtSoLoX → QComboBox → DÙNG clearEditText() HOẶC setCurrentIndex(-1)
        combo = getattr(self.ui, f'txtSoLo{idx}')
        combo.clearEditText()           # XÓA TEXT HIỆN TẠI
        combo.setCurrentIndex(-1)       # KHÔNG CHỌN GÌ

        #Disable nút tắt in
        btn_tat_in = getattr(self.ui, f'btnTatIn{idx}', None)
        if btn_tat_in:
            btn_tat_in.setEnabled(False)
    #----------------------------------------------------------------------------------
    #Hiển thị camera
    def setup_camera_buttons(self):
        """Thiết lập sự kiện cho các nút camera"""
        camera_buttons = [
            self.ui.btnCamera1,
            self.ui.btnCamera2,
            self.ui.btnCamera3,
            self.ui.btnCamera4
        ]

        for idx, button in enumerate(camera_buttons, 1):
            button.clicked.connect(lambda checked, machine_num=idx: self.show_camera(machine_num))

    def setup_chi_tiet_buttons(self):
        """Kết nối các nút btnChiTiet1..4 để mở form ChiTiet.ui"""
        buttons = [
            getattr(self.ui, 'btnChiTiet1', None),
            getattr(self.ui, 'btnChiTiet2', None),
            getattr(self.ui, 'btnChiTiet3', None),
            getattr(self.ui, 'btnChiTiet4', None),
        ]
        for idx, btn in enumerate(buttons, 1):
            if btn:
                # capture idx default to avoid late-binding issue in lambda
                btn.clicked.connect(lambda checked=False, i=idx: show_chi_tiet_dialog(self.window, i))
    #-------------------------------------------------------------------------------------
    #Chọn chứng từ
    def setup_them_chung_tu_buttons(self):
        """Thiết lập sự kiện cho các nút + Chứng Từ"""
        buttons = [
            self.ui.btnThemChungTu1,
            self.ui.btnThemChungTu2,
            self.ui.btnThemChungTu3,
            self.ui.btnThemChungTu4
        ]
        
        for idx, button in enumerate(buttons, 1):
            button.clicked.connect(lambda checked=False, midx=idx: self.mo_man_hinh_chon_chung_tu(midx))

    def mo_man_hinh_chon_chung_tu(self, machine_idx):
        """Mở form chọn chứng từ"""
        self.chon_form = ChungTuForm(self, machine_idx)  # Truyền self và machine_idx
        self.chon_form.selected_signal.connect(lambda data: self.fill_du_lieu_chung_tu(data, machine_idx))
        self.chon_form.show()

    def fill_du_lieu_chung_tu(self, data, machine_idx):
        """Điền dữ liệu chứng từ + LƯU ID CHỨNG TỪ để dùng sau"""
        try:
            # 1. Lưu ID chứng từ vào mảng theo machine_idx
            document_no = data.get('documentno')  # hoặc 'chung_tu_id', 'so_ct', tùy bạn
            if document_no is not None:
                self.chung_tu_ids[machine_idx] = str(document_no)  # ép str để an toàn
                print(f"[MÁY {machine_idx}] Đã lưu ID chứng từ: {document_no}")
            else:
                print(f"[MÁY {machine_idx}] Cảnh báo: Không có ID chứng từ trong data!")
                self.chung_tu_ids[machine_idx] = None

            # 2. Điền dữ liệu vào các field (giữ nguyên như cũ)
            getattr(self.ui, f'txtBienSoXe{machine_idx}').setText(data['bien_so'])
            getattr(self.ui, f'txtSanPham{machine_idx}').setText(data['san_pham'])
            getattr(self.ui, f'txtSLCatLenh{machine_idx}').setText(data['sl_cat_lenh'])
            getattr(self.ui, f'txtSLThucXuat{machine_idx}').setText(data['sl_cat_lenh'])
            getattr(self.ui, f'txtMaIn{machine_idx}').setText(data['ma_in'])

        except Exception as e:
            print(f"Lỗi khi điền dữ liệu chứng từ: {e}")
            QMessageBox.critical(self.window, "Lỗi", f"Không thể điền dữ liệu chứng từ:\n{e}")
    #-------------------------------------------------------------------------------------
    #Tính bao dự tính
    def setup_sl_thuc_xuat_events(self):
        """Thiết lập sự kiện textChanged cho các txtSLThucXuat"""
        for idx in range(1, 5):
            txt_sl_thuc_xuat = getattr(self.ui, f'txtSLThucXuat{idx}')
            txt_bao_du_tinh = getattr(self.ui, f'txtBaoDuTinh{idx}')
            
            # Kết nối sự kiện textChanged
            txt_sl_thuc_xuat.textChanged.connect(
                lambda text, bao_du_tinh=txt_bao_du_tinh: self.tinh_bao_du_tinh(text, bao_du_tinh)
            )

    def tinh_bao_du_tinh(self, sl_thuc_xuat_text, txt_bao_du_tinh):
        """Tính bao dự tính từ số lượng thực xuất"""
        try:
            # Kiểm tra nếu text không rỗng và là số
            if sl_thuc_xuat_text.strip() and sl_thuc_xuat_text.replace('.', '').isdigit():
                sl_thuc_xuat = float(sl_thuc_xuat_text)
                bao_du_tinh = sl_thuc_xuat * 20  # Nhân với 20
                txt_bao_du_tinh.setText(str(int(bao_du_tinh)))  # Chuyển thành số nguyên
            else:
                txt_bao_du_tinh.setText('0')
        except ValueError:
            txt_bao_du_tinh.setText('0')
    #-------------------------------------------------------------------------------------
    #Lấy số lô từ oracle
    def setup_so_lo_combobox(self):
        for idx in range(1, 5):
            combo_box = getattr(self.ui, f'txtSoLo{idx}')
            
            # Thiết lập chế độ có thể edit
            combo_box.setEditable(True)

            combo_box.setStyleSheet("""
                QComboBox {
                    font-family: Calibri;
                    font-size: 18pt;
                    font-weight: bold;
                }
                QComboBox QAbstractItemView {
                    font-family: Calibri;
                    font-size: 18pt;
                    font-weight: bold;
                    background-color: white;
                    selection-background-color: #e6f3ff;
                    outline: none;
                    border: 1px solid #cccccc;
                }
                QComboBox QAbstractItemView::item {
                    min-height: 30px;  /* TĂNG CHIỀU CAO MỖI DÒNG TRONG LIST */
                    padding: 3px;
                }
            """)

            # Tạo QCompleter - tự động xử lý tìm kiếm
            completer = QtWidgets.QCompleter(self.tat_ca_so_lo, combo_box)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
            
            completer.popup().setStyleSheet("""
                QListView {
                    font-family: Calibri;
                    font-size: 18pt;
                    font-weight: bold;
                }
            """)

            combo_box.setCompleter(completer)

    def load_tat_ca_so_lo(self):
        """Tải tất cả số lô từ database"""
        try:
            conn = self.conn_oracle()
            if not conn:
                print("Không thể kết nối Oracle để lấy dữ liệu số lô")
                return []

            cursor = conn.cursor()
            sql = """
            SELECT DISTINCT name 
            FROM M_SoLo          
            WHERE name IS NOT NULL 
            ORDER BY name ASC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            so_lo_list = [row[0] for row in rows if row[0]]
            
            # Lưu danh sách tất cả số lô để sử dụng sau này
            self.tat_ca_so_lo = so_lo_list
            
            return so_lo_list
            
        except Exception as e:
            print(f"Lỗi khi tải dữ liệu số lô: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def tim_kiem_so_lo(self, search_text, combo_box):
        """Tìm kiếm số lô dựa trên text nhập vào"""
        if not hasattr(self, 'tat_ca_so_lo'):
            # Nếu chưa có dữ liệu, tải tất cả số lô trước
            self.tat_ca_so_lo = self.load_tat_ca_so_lo()
        
        if not search_text.strip():
            # Nếu text rỗng, hiển thị tất cả số lô
            combo_box.clear()
            if self.tat_ca_so_lo:
                combo_box.addItems(self.tat_ca_so_lo)
            return
        
        # Tìm kiếm số lô chứa text nhập vào (không phân biệt hoa thường)
        search_text_lower = search_text.lower()
        ket_qua = [so_lo for so_lo in self.tat_ca_so_lo 
                if search_text_lower in so_lo.lower()]
        
        # Cập nhật combobox với kết quả tìm kiếm
        combo_box.clear()
        combo_box.addItems(ket_qua)
        
        # Giữ text đang nhập
        combo_box.setEditText(search_text)
    #-------------------------------------------------------------------------------------
    #Lấy máng xuất từ oracle
    def load_mang_xuat_data(self):
        """Lấy dữ liệu máng xuất từ database và gán vào các comboBox txtMangXuat"""
        try:
            conn = self.conn_oracle()
            if not conn:
                print("Không thể kết nối Oracle để lấy dữ liệu máng xuất")
                return

            cursor = conn.cursor()
            sql = """
            SELECT name FROM M_DMNoiXuatHang 
            WHERE code LIKE 'MX_' OR code = 'CN' OR code = 'CX' 
            ORDER BY name ASC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            # Lấy danh sách tên máng xuất
            mang_xuat_list = [row[0] for row in rows if row[0]]
            
            # Gán dữ liệu vào tất cả các comboBox txtMangXuat
            for idx in range(1, 5):
                combo_box = getattr(self.ui, f'txtMangXuat{idx}')
                combo_box.clear()  # Xóa dữ liệu cũ
                combo_box.addItems(mang_xuat_list)  # Thêm danh sách mới
            
        except Exception as e:
            print(f"Lỗi khi tải dữ liệu máng xuất: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    #-------------------------------------------------------------------------------------
    #Lấy số chứng từ đã lưu local của từng máy
    def lay_chung_tu_id(self, machine_idx):
        """Lấy ID chứng từ đã lưu cho máy in"""
        return self.chung_tu_ids[machine_idx]
    #-------------------------------------------------------------------------------------
    #Cập nhật dữ liệu bật in
    #1. Cập nhật oracle
    
    def cap_nhat_oracle_bat_in(self, idx):
        """Cập nhật FromTime = SYSDATE trong Oracle khi BẬT IN"""
        chung_tu_id = self.lay_chung_tu_id(idx)
        if not chung_tu_id:
            print(f"[MÁY {idx}] LỖI: Không có số chứng từ để cập nhật Oracle!")
            QMessageBox.critical(self.window, "Lỗi DB", "Không có số chứng từ để cập nhật thời gian bắt đầu!")
            return False

        conn = self.conn_oracle()
        if not conn:
            QMessageBox.critical(self.window, "Lỗi Kết Nối", "Không thể kết nối Oracle để cập nhật FromTime!")
            return False

        try:
            cursor = conn.cursor()
            sql = """
            UPDATE M_CommandLatching
            SET FromTime = SYSDATE
            WHERE documentno = :ChungTu
            """
            cursor.execute(sql, ChungTu=chung_tu_id)
            conn.commit()

            if cursor.rowcount == 0:
                print(f"[MÁY {idx}] CẢNH BÁO: Không tìm thấy chứng từ {chung_tu_id} để cập nhật FromTime")
                QMessageBox.warning(self.window, "Cảnh báo", f"Không tìm thấy chứng từ {chung_tu_id} trong hệ thống!")
                return False
            else:
                return True

        except Exception as e:
            print(f"[MÁY {idx}] LỖI Oracle khi cập nhật FromTime: {e}")
            QMessageBox.critical(self.window, "Lỗi DB", f"Cập nhật thời gian bắt đầu thất bại:\n{e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    #2. Cập nhật log
    def ghi_log_bat_in(self, idx):
        """Ghi log vào SQLite khi BẬT IN - dùng connection từ ConnectDB"""
        try:
            # Lấy dữ liệu từ UI
            txtMaIn = getattr(self.ui, f'txtMaIn{idx}')
            txtBaoDuTinh = getattr(self.ui, f'txtBaoDuTinh{idx}')

            ma_in = txtMaIn.text().strip()
            tong_bao = txtBaoDuTinh.text().strip()

            # Ép kiểu an toàn
            try:
                tong_bao_int = int(tong_bao) if tong_bao.isdigit() else 0
            except:
                tong_bao_int = 0

            # Dữ liệu log
            log_data = {
                'PrinterID': f'Máy {idx}',
                'Event': 'BẬT IN',
                'PrintCode': ma_in or 'N/A',
                'TotalPrintQuantity': tong_bao_int,
                'PrintedQuantity': 0,
                'ErrorQuantity': 0,
                'Timestamp': QDateTime.currentDateTime().toString("HH:mm:ss dd-MM-yyyy")
            }

            # DÙNG HÀM TỪ ConnectDB
            conn = get_sqlite_log_connection()
            if not conn:
                print(f"[LỖI LOG] Không thể kết nối SQLite (log.db) cho máy {idx}")
                QMessageBox.critical(self.window, "Lỗi Log", "Không thể kết nối file log.db!")
                return

            cursor = conn.cursor()

            # Insert log
            sql = '''
            INSERT INTO log 
            (PrinterID, Event, PrintCode, TotalPrintQuantity, PrintedQuantity, ErrorQuantity, Timestamp)
            VALUES (:PrinterID, :Event, :PrintCode, :TotalPrintQuantity, :PrintedQuantity, :ErrorQuantity, :Timestamp)
            '''
            cursor.execute(sql, log_data)
            conn.commit()

        except Exception as e:
            print(f"[LỖI LOG] Ghi log BẬT IN thất bại (Máy {idx}): {e}")
            QMessageBox.critical(self.window, "Lỗi Log", f"Ghi log thất bại:\n{e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    #-------------------------------------------------------------------------------------
    #Cập nhật dữ liệu tắt in
    #1. Cập nhật oracle
    def cap_nhat_oracle_tat_in(self, idx):
        """Cập nhật Oracle khi TẮT IN - có kiểm tra tồn tại"""
        try:
            # 1. Lấy dữ liệu từ UI
            chung_tu_id = self.lay_chung_tu_id(idx)
            if not chung_tu_id:
                QMessageBox.warning(self.window, "Lỗi", "Không có số chứng từ để cập nhật!")
                return False

            txtSoLo = getattr(self.ui, f'txtSoLo{idx}')
            txtMangXuat = getattr(self.ui, f'txtMangXuat{idx}')
            txtSLThucXuat = getattr(self.ui, f'txtSLThucXuat{idx}')

            so_lo_name = txtSoLo.currentText().strip() if hasattr(txtSoLo, 'currentText') else txtSoLo.text().strip()
            mang_xuat_name = txtMangXuat.currentText().strip() if hasattr(txtMangXuat, 'currentText') else txtMangXuat.text().strip()
            sl_thuc_xuat = txtSLThucXuat.text().strip()

            # Ép kiểu SL thực xuất
            try:
                qty_out = float(sl_thuc_xuat) if sl_thuc_xuat.replace('.', '').isdigit() else 0
            except:
                qty_out = 0

            # 2. Kiểm tra Số Lô tồn tại
            so_lo_id = self.kiem_tra_ton_tai("M_SoLo", "M_SoLo_ID", "Name", so_lo_name)
            if not so_lo_id:
                QMessageBox.warning(
                    self.window,
                    "Lỗi Dữ Liệu",
                    f"<b>Số Lô '{so_lo_name}' không tồn tại!</b><br>"
                    "Vui lòng kiểm tra lại và <u>tắt in lại</u> sau khi sửa."
                )
                return False

            # 3. Kiểm tra Máng Xuất tồn tại
            mang_xuat_id = self.kiem_tra_ton_tai("M_DMNoiXuatHang", "M_DMNoiXuatHang_ID", "Name", mang_xuat_name)
            if not mang_xuat_id:
                QMessageBox.warning(
                    self.window,
                    "Lỗi Dữ Liệu",
                    f"<b>Máng Xuất '{mang_xuat_name}' không tồn tại!</b><br>"
                    "Vui lòng kiểm tra lại và <u>tắt in lại</u> sau khi sửa."
                )
                return False

            # 4. Cập nhật Oracle
            conn = self.conn_oracle()
            if not conn:
                QMessageBox.critical(self.window, "Lỗi DB", "Không thể kết nối Oracle!")
                return False

            cursor = conn.cursor()
            sql_update = """
            UPDATE M_CommandLatching
            SET
                M_DMNoiXuatHang_ID = :MangXuat,
                M_SoLo_ID = :SoLo,
                QtyOut = :TamXuat,
                ToTime = SYSDATE,
                IsBalance = 'Y'
            WHERE documentno = :ChungTu
            """
            cursor.execute(sql_update, {
                'MangXuat': mang_xuat_id,
                'SoLo': so_lo_id,
                'TamXuat': qty_out,
                'ChungTu': chung_tu_id
            })
            conn.commit()

            if cursor.rowcount == 0:
                QMessageBox.warning(self.window, "Cảnh báo", f"Không tìm thấy chứng từ {chung_tu_id} để cập nhật!")
                conn.close()
                return False
            conn.close()

            # 5. Thành công → Reset giao diện + đổi trạng thái
            self.refresh_field(idx)
            status_label = getattr(self.ui, f'txtTrangThai{idx}')
            status_label.setText("DỪNG IN")

            return True

        except Exception as e:
            print(f"[LỖI] Cập nhật kết thúc in (Máy {idx}): {e}")
            QMessageBox.critical(self.window, "Lỗi DB", f"Cập nhật thất bại:\n{e}")
            return False
    #2. Kiểm tra solo và mangxuat tồn tại
    def kiem_tra_ton_tai(self, table_name, id_column, name_column, name_value):
        """Kiểm tra tên tồn tại → trả về ID, không thì None"""
        if not name_value:
            return None

        conn = self.conn_oracle()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            sql = f"SELECT {id_column} FROM {table_name} WHERE {name_column} = :name"
            cursor.execute(sql, name=name_value)
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Lỗi kiểm tra tồn tại {table_name}: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    #3. Cập nhật sqlite
    def ghi_log_tat_in(self, idx):
        """Ghi log vào SQLite khi TẮT IN - dùng get_sqlite_log_connection()"""
        try:
            # Lấy dữ liệu từ UI
            txtMaIn = getattr(self.ui, f'txtMaIn{idx}')
            txtBaoDuTinh = getattr(self.ui, f'txtBaoDuTinh{idx}')
            txtBaoDangIn = getattr(self.ui, f'txtBaoDangIn{idx}')

            ma_in = txtMaIn.text().strip()
            tong_bao_text = txtBaoDuTinh.text().strip()
            da_in_text = txtBaoDangIn.text().strip()

            # Ép kiểu an toàn
            try:
                tong_bao = int(tong_bao_text) if tong_bao_text.isdigit() else 0
            except:
                tong_bao = 0

            try:
                da_in = int(da_in_text) if da_in_text.isdigit() else 0
            except:
                da_in = 0

            # Dữ liệu log
            log_data = {
                'PrinterID': f'Máy {idx}',
                'Event': 'TẮT IN',
                'PrintCode': ma_in or 'N/A',
                'TotalPrintQuantity': tong_bao,
                'PrintedQuantity': da_in,
                'ErrorQuantity': 0,
                'Timestamp': QDateTime.currentDateTime().toString("HH:mm:ss dd-MM-yyyy")
            }

            # DÙNG HÀM TỪ ConnectDB
            conn = get_sqlite_log_connection()
            if not conn:
                print(f"[LỖI LOG] Không thể kết nối SQLite (X:\\log.db) cho máy {idx}")
                QMessageBox.critical(self.window, "Lỗi Log", "Không thể kết nối file log.db!")
                return False

            cursor = conn.cursor()

            # Insert log TẮT IN
            sql = '''
            INSERT INTO log 
            (PrinterID, Event, PrintCode, TotalPrintQuantity, PrintedQuantity, ErrorQuantity, Timestamp)
            VALUES (:PrinterID, :Event, :PrintCode, :TotalPrintQuantity, :PrintedQuantity, :ErrorQuantity, :Timestamp)
            '''
            cursor.execute(sql, log_data)
            conn.commit()
            return True

        except Exception as e:
            print(f"[LỖI LOG] Ghi log TẮT IN thất bại (Máy {idx}): {e}")
            QMessageBox.critical(self.window, "Lỗi Log", f"Ghi log thất bại:\n{e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    #-------------------------------------------------------------------------------------
    #Bật In
    def setup_bat_in_buttons(self):
        """Thiết lập sự kiện cho các nút Bật In"""
        buttons = [
            self.ui.btnBatIn1,
            self.ui.btnBatIn2,
            self.ui.btnBatIn3,
            self.ui.btnBatIn4
        ]
        for idx, button in enumerate(buttons, 1):
            button.clicked.connect(lambda checked=False, midx=idx: self.xu_ly_bat_in(midx))

    def xu_ly_bat_in(self, idx):
        """Xử lý logic khi nhấn nút Bật In cho máy in idx"""
        try:
            # Lấy các widget theo idx
            txtBienSoXe = getattr(self.ui, f'txtBienSoXe{idx}')
            txtSoLo = getattr(self.ui, f'txtSoLo{idx}')
            txtSLThucXuat = getattr(self.ui, f'txtSLThucXuat{idx}')
            txtMangXuat = getattr(self.ui, f'txtMangXuat{idx}')
            txtMaIn = getattr(self.ui, f'txtMaIn{idx}')
            txtBaoDuTinh = getattr(self.ui, f'txtBaoDuTinh{idx}')

            bien_so = txtBienSoXe.text().strip()
            so_lo = txtSoLo.currentText().strip() if hasattr(txtSoLo, 'currentText') else txtSoLo.text().strip()
            sl_thuc_xuat = txtSLThucXuat.text().strip()
            mang_xuat = txtMangXuat.currentText().strip() if hasattr(txtMangXuat, 'currentText') else txtMangXuat.text().strip()
            ma_in = txtMaIn.text().strip()
            bao_du_tinh = txtBaoDuTinh.text().strip()
            chung_tu = self.chung_tu_ids[idx]

            # === BƯỚC 1: KIỂM TRA TRẠNG THÁI MÁY IN ===
            if getattr(self.ui, f'txtTrangThai{idx}').text().strip().upper() == "ĐANG IN":
                # Previously showed a modal info box; now just log
                print(f"[INFO] Máy {idx} đang hoạt động, bỏ qua lệnh Bật In")
                return

            # === BƯỚC 2: KIỂM TRA DỮ LIỆU ===
            in_dac_biet = not chung_tu  # Không có chứng từ → in đặc biệt

            if in_dac_biet:
                # Chỉ cần mã in + số lượng
                if not ma_in or bao_du_tinh == "0":
                    # Previously used QMessageBox.warning; now log
                    print(f"[WARNING] Vui lòng nhập mã in và số lượng thực xuất (Máy {idx})")
                    return
            else:
                # In bình thường → kiểm tra đầy đủ
                if not bien_so:
                    print(f"[WARNING] Vui lòng nhập biển số xe (Máy {idx})")
                    return
                thieu = []
                if not so_lo: thieu.append("Số Lô")
                if not sl_thuc_xuat: thieu.append("SL Thực Xuất")
                if not mang_xuat: thieu.append("Máng Xuất")
                if not ma_in: thieu.append("Mã In")
                if bao_du_tinh == "0": thieu.append("Số lượng thực xuất")
                if thieu:
                    print(f"[WARNING] Thiếu thông tin: {', '.join(thieu)} (Máy {idx})")
                    return

            # === BƯỚC 3: KẾT NỐI MÁY IN ===
            if not self.connect_to_printer(idx):
                return
            client = self.printer_clients[idx]

            # === BƯỚC 4: GỬI LỆNH BẬT IN ===
            cmd_t = f"\x02T020001025800000{ma_in}\x03".encode('utf-8')
            client.send_raw(cmd_t)
            client.send("RA")
            client.send("O1")

            # === BƯỚC 5: CẬP NHẬT GIAO DIỆN ===
            getattr(self.ui, f'txtTrangThai{idx}').setText("ĐANG IN")

            # === BƯỚC 6: GHI LOG & ORACLE ===
            self.ghi_log_bat_in(idx)
            if chung_tu:
                self.cap_nhat_oracle_bat_in(idx)
        except Exception as e:
            print(f"Lỗi bật in máy {idx}: {e}")
            QMessageBox.critical(self.window, "Lỗi", f"Đã xảy ra lỗi khi bật in:\n{e}")

    def bat_dau_in_binh_thuong(self, idx):
        """Hàm in bình thường"""
        chung_tu_id = self.lay_chung_tu_id(idx)
        if not chung_tu_id:
            # Was a warning dialog; now log and return
            print(f"[WARNING] Chưa chọn chứng từ hợp lệ cho máy {idx}")
            return

        # 1. Cập nhật Oracle
        if not self.cap_nhat_oracle_bat_in(idx):
            return  # Nếu cập nhật thất bại → dừng in
        
        if not self.ghi_log_bat_in(idx):
            return

        # # 2. Tiếp tục in (no modal on success)
        # print(f"[INFO] Đang in bình thường cho máy {idx}, chứng từ: {chung_tu_id}")

    def bat_dau_in_dac_biet(self, idx):
        """Hàm in đặc biệt - sẽ triển khai sau"""
        # Do not show modal info; log instead
        print(f"[INFO] In đặc biệt (không biển số) cho máy {idx}...")
        # TODO: In mẫu đặc biệt, không có biển số
    #-------------------------------------------------------------------------------------
    #Tắt In
    def setup_tat_in_buttons(self):
        """Thiết lập sự kiện cho các nút Tắt In"""
        buttons = [
            self.ui.btnTatIn1,
            self.ui.btnTatIn2,
            self.ui.btnTatIn3,
            self.ui.btnTatIn4
        ]
        for idx, button in enumerate(buttons, 1):
            button.clicked.connect(lambda checked=False, midx=idx: self.xu_ly_tat_in(midx))
    
    def xu_ly_tat_in(self, idx):
        """Xử lý khi nhấn Tắt In - phân biệt In Bình Thường và In Đặc Biệt"""
        try:
            status_label = getattr(self.ui, f'txtTrangThai{idx}')
            if status_label.text().strip().upper() != "ĐANG IN":
                QMessageBox.information(self.window, "Thông báo", "Máy in chưa ở trạng thái ĐANG IN!")
                return

            # === LẤY DỮ LIỆU ===
            ma_in = getattr(self.ui, f'txtMaIn{idx}').text().strip()
            bao_du_tinh = getattr(self.ui, f'txtBaoDuTinh{idx}').text().strip()
            bao_dang_in = getattr(self.ui, f'txtBaoDangIn{idx}').text().strip()
            so_lo = getattr(self.ui, f'txtSoLo{idx}').currentText().strip()
            mang_xuat = getattr(self.ui, f'txtMangXuat{idx}').currentText().strip()
            chung_tu = self.chung_tu_ids[idx] or ""

            in_dac_biet = not chung_tu

            # === GỬI LỆNH TẮT IN ===
            client = self.printer_clients[idx]
            if client and client.socket:
                client.send("O0")

            # === HỎI RÁCH/THỪA (chỉ khi in bình thường + có bao) ===
            if not in_dac_biet and bao_dang_in != "0":
                form = BaoRachVoForm(idx)
                if form.exec() == QDialog.DialogCode.Accepted:
                    # Lấy dữ liệu từ form
                    hanh_dong = form.hanh_dong
                    bao_rach = form.bao_rach
                    bao_thua = form.bao_thua
                    self.xu_ly_sau_tat_in(idx, hanh_dong, bao_rach, bao_thua, ma_in, bao_du_tinh, bao_dang_in, so_lo, mang_xuat, chung_tu)
                else:
                    return  # Hủy → không tắt
            else:
                # Tắt ngay (in đặc biệt hoặc không có bao)
                self.xu_ly_sau_tat_in(idx, 1, "0", "0", ma_in, bao_du_tinh, bao_dang_in, so_lo, mang_xuat, chung_tu)

        except Exception as e:
            print(f"[LỖI] Tắt in máy {idx}: {e}")
            QMessageBox.critical(self.window, "Lỗi", f"Tắt in thất bại:\n{e}")

    def xu_ly_sau_tat_in(self, idx, hanh_dong, bao_rach, bao_thua, ma_in, bao_du_tinh, bao_dang_in, so_lo, mang_xuat, chung_tu):
        try:
            if hanh_dong == 1:
                self.ghi_log_tat_in(idx)
                if bao_rach != "0":
                    self._ghi_log(idx, "BÁO RÁCH", ma_in, bao_du_tinh, bao_rach)
                if chung_tu:
                    self.cap_nhat_oracle_tat_in(idx)
            else:
                self._ghi_log(idx, "TẠM DỪNG", ma_in, bao_du_tinh, bao_dang_in)

            self.refresh_field(idx)
            getattr(self.ui, f'txtTrangThai{idx}').setText("DỪNG IN")
            self.chung_tu_ids[idx] = None

            if self.printer_clients[idx]:
                self.printer_clients[idx].stop()
                self.printer_clients[idx] = None

            QMessageBox.information(self.window, "Thành công", f"Đã tắt in máy {idx}!")

        except Exception as e:
            print(f"Lỗi xử lý sau tắt in: {e}")
    #-------------------------------------------------------------------------------------
    #Tắt In
    def load_printer_ips(self):
        """Tương đương LoadIPs() + GetPriterIp()"""
        try:
            conn = get_sqlite_printer_connection()
            if not conn:
                return
            cursor = conn.cursor()
            cursor.execute("SELECT id, ip FROM printer WHERE id BETWEEN 1 AND 4")
            for row in cursor.fetchall():
                idx, ip = row
                self.printer_ips[idx] = ip.strip()
            conn.close()
        except Exception as e:
            print(f"Lỗi tải IP: {e}")

    def connect_to_printer(self, idx):
        """Tương đương StartClient()"""
        ip = self.printer_ips[idx]
        if not ip:
            QMessageBox.warning(self.window, "Lỗi", f"Chưa cấu hình IP máy {idx}")
            return False

        if self.printer_clients[idx]:
            try:
                if self.printer_clients[idx].socket and self.printer_clients[idx].socket.fileno() != -1:
                    return True
            except:
                pass

        client = PrinterClient(idx, ip)
        if client.connect():
            client.data_received.connect(self.on_printer_data)
            client.disconnected.connect(self.on_printer_disconnected)
            client.start()
            self.printer_clients[idx] = client
            return True
        else:
            QMessageBox.critical(self.window, "Lỗi", f"Không kết nối được máy {idx}\nIP: {ip}")
            return False

    def on_printer_data(self, idx, data):
        """Xử lý dữ liệu từ máy in"""
        if len(data) == 11:
            try:
                bao = int(data[1:9])
                current = int(getattr(self.ui, f'txtBaoDaIn{idx}').text() or "0")
                total = current + bao
                getattr(self.ui, f'txtBaoDangIn{idx}').setText(str(total))
            except:
                pass
        elif len(data) == 10:
            status = data[7]
            label = getattr(self.ui, f'txtTrangThai{idx}')
            new_status = "ĐANG IN" if status in "13579" else "DỪNG IN"
            if label.text() != new_status:
                label.setText(new_status)

    def on_printer_disconnected(self, idx):
        """Máy in mất kết nối"""
        print(f"[MÁY {idx}] Mất kết nối")
        self.printer_clients[idx] = None
        getattr(self.ui, f'txtTrangThai{idx}').setText("DỪNG IN")

    def update_bao_cycle(self):
        """Gửi GA + E cho từng máy"""
        if not self.printer_clients[self.current_machine_check]:
            self.current_machine_check = (self.current_machine_check % 4) + 1
            return

        client = self.printer_clients[self.current_machine_check]
        if client and client.socket:
            client.send("GA")
            client.send("E")

        self.current_machine_check = (self.current_machine_check % 4) + 1
    #-------------------------------------------------------------------------------------
    #Tìm kiếm mã in đang in dở
    def setup_ma_in_events(self):
        """Kết nối sự kiện textChanged cho các txtMaIn1..txtMaIn4"""
        for idx in range(1, 5):
            widget = getattr(self.ui, f'txtMaIn{idx}', None)
            if widget:
                widget.textChanged.connect(lambda text, i=idx: self.on_ma_in_changed(text, i))

    def on_ma_in_changed(self, text: str, machine_idx: int):
        try:
            if not text or len(text.strip()) < 6:
                return
            search_key = text.strip()[1:]
            if not search_key:
                return

            conn = get_sqlite_pause_print_connection()
            if not conn:
                print("Không thể mở DB pause_print_information")
                return
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            try:
                cur.execute("SELECT MaIn, BaoDaIn, ChungTu FROM information WHERE MaIn LIKE ? ORDER BY Date LIMIT 1", ('%'+search_key,))
                row = cur.fetchone()
            except sqlite3.Error as e:
                print("Lỗi truy vấn pause DB:", e)
                row = None

            if not row:
                return

            db_main = row['MaIn'] if 'MaIn' in row.keys() else None
            bao_da_in = row['BaoDaIn'] if 'BaoDaIn' in row.keys() else None
            chungtu = row['ChungTu'] if 'ChungTu' in row.keys() else None

            if not db_main:
                return

            # suffix (từ ký tự 2 trở đi)
            db_suffix = db_main[1:] if len(db_main) > 1 else db_main

            # Lấy code ca hiện tại
            ca_text = self.ui.LabelShift.text().strip() if hasattr(self.ui, 'LabelShift') else 'CA 1'
            ca_code = {"CA 1": "A", "CA 2": "B", "CA 3": "C"}.get(ca_text, "A")
            new_ma = ca_code + db_suffix

            # Cập nhật txtMaIn (block signals để tránh loop)
            ma_widget = getattr(self.ui, f'txtMaIn{machine_idx}', None)
            if ma_widget and ma_widget.text() != new_ma:
                ma_widget.blockSignals(True)
                ma_widget.setText(new_ma)
                ma_widget.blockSignals(False)

            # Cập nhật BaoDaIn
            bao_widget = getattr(self.ui, f'txtBaoDaIn{machine_idx}', None)
            if bao_widget and bao_da_in is not None:
                try:
                    bao_widget.setText(str(bao_da_in))
                except Exception:
                    pass

            # Lưu chung_tu
            if chungtu is not None:
                try:
                    self.chung_tu_ids[machine_idx] = str(chungtu)
                    print(f"[MÁY {machine_idx}] Lấy chung_tu từ pause DB: {chungtu}")
                except Exception:
                    pass

        except Exception as e:
            print(f"Lỗi khi xử lý txtMaIn thay đổi (Máy {machine_idx}): {e}")
        finally:
            try:
                cur.close()
            except:
                pass
            try:
                conn.close()
            except:
                pass
