# camera_viewer.py
import cv2
import subprocess
import platform
import re
from PyQt6.QtWidgets import QGraphicsScene, QMessageBox
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtCore import QTimer, Qt

class CameraViewer:
    def __init__(self, window, rtsp_url):
        self.window = window
        self.rtsp_url = rtsp_url
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Setup QGraphicsView
        self.scene = QGraphicsScene()
        self.window.graphicsView.setScene(self.scene)

        # Bắt đầu hiển thị
        self.start_camera()

    def extract_ip(self):
        match = re.search(r'@([\d\.]+)', self.rtsp_url)
        return match.group(1) if match else None

    def ping_ip(self, ip):
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

    def start_camera(self):
        """Khởi động camera với xử lý lỗi chi tiết"""
        ip = self.extract_ip()
        if not ip:
            self.show_error("❌ LỖI: Không thể trích xuất IP từ RTSP URL!")
            return False
            
        # Ping kiểm tra kết nối mạng
        if not self.ping_ip(ip):
            self.show_error(f"❌ MẤT KẾT NỐI MẠNG\nIP: {ip}\n\nKiểm tra:\n• Kết nối mạng\n• Địa chỉ IP\n• Tường lửa")
            return False

        # Thử kết nối camera
        try:
            self.cap = cv2.VideoCapture(self.rtsp_url)
            if not self.cap.isOpened():
                self.show_error(
                    f"⚠️ KHÔNG MỞ ĐƯỢC CAMERA\n\n"
                    f"IP: {ip}\n"
                    f"RTSP: {self.rtsp_url}\n\n"
                    f"Nguyên nhân:\n"
                    f"• Sai thông tin đăng nhập\n"
                    f"• Port bị chặn\n"
                    f"• Camera không hỗ trợ RTSP"
                )
                return False

            # Test đọc frame đầu tiên
            ret, frame = self.cap.read()
            if not ret:
                self.show_error("📷 CAMERA KHÔNG GỬI DỮ LIỆU\n\nKiểm tra:\n• Camera có bật không?\n• Luồng video có tồn tại?")
                self.cap.release()
                return False

            # Khởi động timer nếu thành công
            self.timer.start(30)
            return True

        except Exception as e:
            self.show_error(f"🚨 LỖI HỆ THỐNG\n\n{str(e)}")
            return False

    def update_frame(self):
        if not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            # Mất kết nối camera
            ip = self.extract_ip()
            if ip and not self.ping_ip(ip):
                self.timer.stop()
                if self.cap:
                    self.cap.release()
                self.show_error("📡 MẤT KẾT NỐI CAMERA\n\nĐang thử kết nối lại...")
                QTimer.singleShot(5000, self.start_camera)
            return

        # Hiển thị frame
        self.display_frame(frame)

    def display_frame(self, frame):
        """Hiển thị frame lên QGraphicsView"""
        try:
            # Chuyển frame → QImage
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            img = QImage(frame_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)

            # Fit vào QGraphicsView
            self.scene.clear()
            view_size = self.window.graphicsView.size()
            scaled = pixmap.scaled(view_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.scene.addPixmap(scaled)
            
        except Exception as e:
            print(f"Lỗi hiển thị frame: {e}")

    def show_error(self, msg):
        """Hiển thị thông báo lỗi trên graphicsView"""
        self.scene.clear()
        
        # Tạo font lớn hơn cho thông báo lỗi
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        
        # Hiển thị thông báo lỗi
        text_item = self.scene.addText(msg)
        text_item.setDefaultTextColor(Qt.GlobalColor.red)
        text_item.setFont(font)
        
        # Căn giữa thông báo
        text_rect = text_item.boundingRect()
        view_rect = self.scene.sceneRect()
        text_item.setPos(
            (view_rect.width() - text_rect.width()) / 2,
            (view_rect.height() - text_rect.height()) / 2
        )

    def stop(self):
        """Dừng camera và giải phóng tài nguyên"""
        if self.timer.isActive():
            self.timer.stop()
        if self.cap:
            self.cap.release()
        self.scene.clear()