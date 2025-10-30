# main.py
import sys
from PyQt6 import QtWidgets, QtCore, uic

class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Load UI
        uic.loadUi("ManChinh.ui", self)

        # === HIỆN CỬA SỔ TRƯỚC ===
        self.show()

        # === CĂN PHẦN DƯỚI SÁT TASKBAR ===
        QtCore.QTimer.singleShot(100, self.align_bottom_to_taskbar)

    def align_bottom_to_taskbar(self):
        screen = QtWidgets.QApplication.primaryScreen()
        available = screen.availableGeometry()  # Vùng khả dụng (trừ taskbar)

        # Kích thước mong muốn
        desired_width = available.width()
        desired_height = 1012

        # === TÍNH Y ĐỂ PHẦN DƯỚI SÁT TASKBAR ===
        y_pos = available.bottom() - desired_height + 1  # +1 để sát, không chồng

        # Đảm bảo không vượt quá vùng khả dụng
        if y_pos < available.y():
            y_pos = available.y()
            desired_height = available.height()

        # Đặt vị trí + kích thước
        self.setGeometry(
            available.x(),
            y_pos,
            desired_width,
            desired_height
        )

        # Nội dung full
        if self.centralWidget():
            self.centralWidget().setFixedSize(desired_width, desired_height)

        # === TẮT BO GÓC ===
        if self.windowHandle():
            self.apply_corner_fix()

    def apply_corner_fix(self):
        if sys.platform == "win32":
            import ctypes
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_DONOTROUND = 0
            hwnd = int(self.windowHandle().winId())
            try:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                    ctypes.byref(ctypes.c_int(DWMWCP_DONOTROUND)),
                    ctypes.sizeof(ctypes.c_int)
                )
            except:
                pass

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    sys.exit(app.exec())