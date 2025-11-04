# controller.py
from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer, QDateTime, Qt
from PyQt6.QtWidgets import QMenu, QWidgetAction,QMessageBox
from PyQt5 import QtCore
from ChuyenMayInController import MaySelectorWidget
import sqlite3
from ConnectDB import get_oracle_connection, get_oracle_test_connection, get_sqlite_log_connection, get_sqlite_pause_print_connection, get_sqlite_printer_connection, get_sqlite_camera_connection
from HienCameraController import CameraViewer
import subprocess
import platform
from ChonChungTuController import ChungTuForm

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

        self.setup_them_chung_tu_buttons()
        self.cap_nhat_dong_ho()
        self.cap_nhat_ca()
        self.setup_chuyen_may_buttons()
        self.setup_refresh_buttons()
        self.current_camera_viewer = None
        self.setup_camera_buttons()
        self.setup_sl_thuc_xuat_events()
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

                # Các widget cần xử lý
                fields = [
                    f"txtMaIn{idx}", f"txtBienSoXe{idx}", f"txtSanPham{idx}",
                    f"txtSLCatLenh{idx}", f"txtMangXuat{idx}", f"btnRefresh{idx}"
                ]
                buttons = [
                    f"btnThemChungTu{idx}", f"btnBatIn{idx}",
                    f"btnSearchMaIn{idx}", f"btnTatIn{idx}"
                ]

                # ===== ĐANG IN =====
                if status_text == "ĐANG IN":
                    # Làm đỏ gradient label
                    status_label.setStyleSheet("""
                        QLabel {
                            background: qradialgradient(
                                cx:0.5, cy:0.5, radius:0.9,
                                fx:0.5, fy:0.5,
                                stop:0 #cc0000,      /* Tâm: đỏ đậm */
                                stop:0.4 #ff3333,    /* Giữa: đỏ sáng hơn */
                                stop:1 #ffe6e6       /* Viền: đỏ nhạt gần trắng */
                            );
                            color: white;
                            font-weight: bold;
                            border-radius: 6px;
                            padding: 4px;
                            border: 1px solid #b30000;
                        }
                    """)

                    # Khóa các field và nút
                    for field_name in fields:
                        widget = getattr(self.ui, field_name, None)
                        if widget:
                            if hasattr(widget, "setReadOnly"):
                                widget.setReadOnly(True)
                            if hasattr(widget, "setEnabled"):
                                widget.setEnabled(False)

                    # Disable các nút thêm chứng từ, bật in, search mã in
                    for btn_name in buttons[:-1]:  # trừ btnTatIn
                        btn = getattr(self.ui, btn_name, None)
                        if btn:
                            btn.setEnabled(False)

                    # btnTatIn vẫn được bật
                    btn_tat_in = getattr(self.ui, f"btnTatIn{idx}", None)
                    if btn_tat_in:
                        btn_tat_in.setEnabled(True)

                # ===== DỪNG IN =====
                elif status_text == "DỪNG IN":
                    # Trả màu về mặc định
                    status_label.setStyleSheet("")

                    # Disable duy nhất btnTatIn
                    btn_tat_in = getattr(self.ui, f"btnTatIn{idx}", None)
                    if btn_tat_in:
                        btn_tat_in.setEnabled(False)

                    # Các field và nút khác mở lại
                    for field_name in fields:
                        widget = getattr(self.ui, field_name, None)
                        if widget:
                            if hasattr(widget, "setReadOnly"):
                                widget.setReadOnly(False)
                            if hasattr(widget, "setEnabled"):
                                widget.setEnabled(True)
                    for btn_name in buttons[:-1]:
                        btn = getattr(self.ui, btn_name, None)
                        if btn:
                            btn.setEnabled(True)
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

    def ping_ip(self, ip):
        """Ping đến IP để kiểm tra kết nối mạng"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        try:
            result = subprocess.run(
                ['ping', param, '1', ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3
            )
            return result.returncode == 0
        except:
            return False

    def get_camera_info(self, machine_number):
        """Lấy thông tin camera từ database theo số máy in"""
        try:
            conn = sqlite3.connect("camera.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ip_address, rtsp_url FROM cameras 
                WHERE machine_number = ? AND status = 1
            """, (machine_number,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'ip': result[0],
                    'rtsp_url': result[1]
                }
            else:
                print(f"Không tìm thấy thông tin camera cho máy in {machine_number}")
                return None
                
        except sqlite3.Error as e:
            print(f"Lỗi database: {e}")
            return None

    def show_camera(self, machine_number):
        """Hiển thị camera cho máy in được chọn"""
        # Dừng camera hiện tại nếu có
        if self.current_camera_viewer:
            self.current_camera_viewer.stop()
            self.current_camera_viewer = None
        
        # Lấy thông tin camera từ database
        camera_info = self.get_camera_info(machine_number)
        
        if not camera_info:
            QMessageBox.warning(
                self.window, 
                "Lỗi Camera", 
                f"Không tìm thấy thông tin camera cho máy in {machine_number}\n"
                f"Vui lòng kiểm tra cấu hình database."
            )
            return
        
        ip = camera_info['ip']
        rtsp_url = camera_info['rtsp_url']
                
        # Thử ping IP trước khi kết nối camera
        if not self.ping_ip(ip):
            QMessageBox.critical(
                self.window,
                "Lỗi Kết Nối Mạng",
                f"❌ KHÔNG THỂ KẾT NỐI ĐẾN MÁY IN {machine_number}\n\n"
                f"📍 IP: {ip}\n"
                f"🔍 Nguyên nhân:\n"
                f"   • Máy in đang tắt\n"
                f"   • Mất kết nối mạng\n"
                f"   • Sai địa chỉ IP\n"
                f"   • Tường lửa chặn kết nối\n\n"
                f"🛠️ Khắc phục:\n"
                f"   • Kiểm tra nguồn máy in\n"
                f"   • Kiểm tra cáp mạng\n"
                f"   • Liên hệ bộ phận IT"
            )
            return
        
        # Thử kết nối camera
        try:
            self.current_camera_viewer = CameraViewer(self.window, rtsp_url)
            # Kiểm tra xem camera có khởi tạo thành công không
            if not self.current_camera_viewer.cap or not self.current_camera_viewer.cap.isOpened():
                raise Exception("Không thể mở luồng video từ camera")
                
        except Exception as e:
            error_msg = (
                f"⚠️ KHÔNG THỂ HIỂN THỊ CAMERA MÁY IN {machine_number}\n\n"
                f"📍 IP: {ip}\n"
                f"🌐 RTSP: {rtsp_url}\n"
                f"🔍 Nguyên nhân:\n"
                f"   • Camera bị tắt\n"
                f"   • Sai thông tin đăng nhập RTSP\n"
                f"   • Port RTSP bị chặn\n"
                f"   • Camera không hỗ trợ RTSP\n\n"
                f"🛠️ Khắc phục:\n"
                f"   • Kiểm tra nguồn camera\n"
                f"   • Xác nhận URL RTSP\n"
                f"   • Kiểm tra username/password\n"
                f"   • Liên hệ bộ phận camera"
            )
            
            QMessageBox.critical(self.window, "Lỗi Hiển Thị Camera", error_msg)
            
            # Dọn dẹp nếu có lỗi
            if self.current_camera_viewer:
                self.current_camera_viewer.stop()
                self.current_camera_viewer = None
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
                print("Lỗi 1")
                txt_bao_du_tinh.setText('0')
        except ValueError:
            print("Lỗi 2")
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
            conn = get_oracle_connection()
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
            conn = get_oracle_connection()
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

        conn = get_oracle_connection()
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
                print(f"[MÁY {idx}] ĐÃ CẬP NHẬT FromTime cho chứng từ: {chung_tu_id}")
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
                'PrinterID': idx,
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

            print(f"[LOG] Ghi log BẬT IN thành công - Máy {idx}, Mã in: {ma_in}, Tổng bao: {tong_bao_int}")

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
            conn = get_oracle_connection()
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

            print(f"[MÁY {idx}] ĐÃ CẬP NHẬT KẾT THÚC IN - CT: {chung_tu_id}")
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

        conn = get_oracle_connection()
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
                'PrinterID': idx,
                'Event': 'TẮT IN',
                'PrintCode': ma_in or 'N/A',
                'TotalPrintQuantity': tong_bao,
                'PrintedQuantity': da_in,
                'ErrorQuantity': 0,
                'Timestamp': QDateTime.currentDateTime().toString("HH:mm:ss dd/MM/yyyy")
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

            print(f"[LOG] Ghi log TẮT IN thành công - Máy {idx}, Mã in: {ma_in}, Tổng: {tong_bao}, Đã in: {da_in}")
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

            bien_so = txtBienSoXe.text().strip()
            so_lo = txtSoLo.currentText().strip() if hasattr(txtSoLo, 'currentText') else txtSoLo.text().strip()
            sl_thuc_xuat = txtSLThucXuat.text().strip()
            mang_xuat = txtMangXuat.currentText().strip() if hasattr(txtMangXuat, 'currentText') else txtMangXuat.text().strip()

            # BƯỚC 1: Kiểm tra txtBienSoXe
            if not bien_so:
                # Chuyển sang chế độ IN ĐẶC BIỆT
                self.chuyen_che_do_in_dac_biet(idx)
                return

            # BƯỚC 2: Nếu có biển số → kiểm tra 3 ô còn lại
            thieu_cac_o = []
            if not so_lo:
                thieu_cac_o.append("Số Lô")
            if not sl_thuc_xuat:
                thieu_cac_o.append("SL Thực Xuất")
            if not mang_xuat:
                thieu_cac_o.append("Máng Xuất")

            if thieu_cac_o:
                # Tạo thông báo chi tiết
                danh_sach_thieu = ", ".join(thieu_cac_o)
                QMessageBox.warning(
                    self.window,
                    "Thiếu thông tin",
                    f"Vui lòng điền đầy đủ cho ô: <b>{danh_sach_thieu}</b>"
                )
                return

            # TẤT CẢ ĐỦ → Chuyển sang chế độ IN BÌNH THƯỜNG
            self.chuyen_che_do_in_binh_thuong(idx)

        except Exception as e:
            print(f"Lỗi khi xử lý Bật In máy {idx}: {e}")
            QMessageBox.critical(self.window, "Lỗi", f"Đã xảy ra lỗi khi bật in:\n{e}")

    def chuyen_che_do_in_binh_thuong(self, idx):
        """Thực hiện các bước khi đủ dữ liệu → in bình thường"""
        try:
            # Cập nhật trạng thái máy in
            status_label = getattr(self.ui, f'txtTrangThai{idx}')
            status_label.setText("ĐANG IN")
            
            # Có thể thêm: lưu log, gọi hàm in thật, bật timer theo dõi...
            print(f"[MÁY {idx}] Đã chuyển sang chế độ IN BÌNH THƯỜNG")
            
            # Gọi hàm in thực tế (bạn sẽ thêm sau)
            self.bat_dau_in_binh_thuong(idx)

        except Exception as e:
            print(f"Lỗi chuyển chế độ in bình thường máy {idx}: {e}")

    # Chuyển chế độ IN ĐẶC BIỆT
    def chuyen_che_do_in_dac_biet(self, idx):
        """Thực hiện các bước khi không có biển số → in đặc biệt"""
        try:
            status_label = getattr(self.ui, f'txtTrangThai{idx}')
            status_label.setText("ĐANG IN")  # Vẫn hiển thị đang in
            
            print(f"[MÁY {idx}] Đã chuyển sang chế độ IN ĐẶC BIỆT (không có biển số)")
            
            # Gọi hàm in đặc biệt
            self.bat_dau_in_dac_biet(idx)

        except Exception as e:
            print(f"Lỗi chuyển chế độ in đặc biệt máy {idx}: {e}")

    # Hàm in thực tế (sẽ phát triển sau)
    def bat_dau_in_binh_thuong(self, idx):
        """Hàm in bình thường"""
        chung_tu_id = self.lay_chung_tu_id(idx)
        if not chung_tu_id:
            QMessageBox.warning(self.window, "Lỗi", "Chưa chọn chứng từ hợp lệ!")
            return

        # 1. Cập nhật Oracle
        if not self.cap_nhat_oracle_bat_in(idx):
            return  # Nếu cập nhật thất bại → dừng in
        
        if not self.ghi_log_bat_in(idx):
            return

        # 2. Tiếp tục in
        QMessageBox.information(
            self.window,
            "In Bình Thường",
            f"Đang in bình thường cho máy {idx}\nSố chứng từ: {chung_tu_id}\nĐã ghi thời gian bắt đầu."
        )

    def bat_dau_in_dac_biet(self, idx):
        """Hàm in đặc biệt - sẽ triển khai sau"""
        QMessageBox.information(self.window, "In Đặc Biệt", f"Đang in đặc biệt (không biển số) cho máy {idx}...")
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
        """Xử lý khi nhấn Tắt In"""
        status_label = getattr(self.ui, f'txtTrangThai{idx}')
        if status_label.text().strip().upper() != "ĐANG IN":
            QMessageBox.information(self.window, "Thông báo", "Máy in chưa ở trạng thái ĐANG IN!")
            return

        reply = QMessageBox.question(
            self.window,
            "Xác nhận Tắt In",
            f"Bạn có chắc muốn <b>tắt in</b> cho máy {idx}?\n"
            "Dữ liệu sẽ được lưu vào hệ thống.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Gọi cập nhật + log (sẽ thêm log ở bước sau)
            if self.cap_nhat_ket_thuc_in(idx):
                # Thành công → có thể ghi log TẮT IN
                self.ghi_log_tat_in(idx)
                QMessageBox.information(self.window, "Thành công", f"Đã tắt in máy {idx} và lưu dữ liệu!")
            else:
                # Thất bại → vẫn ĐANG IN
                QMessageBox.critical(self.window, "Lỗi", "Tắt in thất bại! Vui lòng kiểm tra lại dữ liệu.")

    