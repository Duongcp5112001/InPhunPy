# controller.py
from PyQt6.QtCore import QTimer, QDateTime
from PyQt6.QtWidgets import QMenu, QWidgetAction,QMessageBox
from PyQt5 import QtCore
from ChuyenMayInController import MaySelectorWidget
import sqlite3
from HienCameraController import CameraViewer
import subprocess
import platform

class Controller:
    def __init__(self, window):
        self.window = window
        self.ui = window

        self.timer_dongho = QTimer()
        self.timer_dongho.timeout.connect(self.cap_nhat_dong_ho)
        self.timer_dongho.start(1000)

        self.cap_nhat_dong_ho()
        self.cap_nhat_ca()
        self.setup_chuyen_may_buttons()
        self.setup_refresh_buttons()
        self.current_camera_viewer = None
        self.setup_camera_buttons()

        self.timer_check_status = QTimer()
        self.timer_check_status.timeout.connect(self.check_trang_thai_may_in)
        self.timer_check_status.start(1000)
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
                    f"txtSLCatLenh{idx}", f"txtSLThucXuat{idx}",
                    f"txtSoLo{idx}", f"txtMangXuat{idx}", f"btnRefresh{idx}"
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
    


    