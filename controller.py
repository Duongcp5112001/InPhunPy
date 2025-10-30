# controller.py
from PyQt6.QtCore import QTimer, QDateTime

class Controller:
    def __init__(self, window):
        self.window = window
        self.ui = window

        # Timer
        self.timer_dongho = QTimer()
        self.timer_dongho.timeout.connect(self.cap_nhat_dong_ho)
        self.timer_dongho.start(1000)

        # Khởi động
        self.cap_nhat_dong_ho()

    def cap_nhat_dong_ho(self):
        current = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
        try:
            self.ui.label_time.setText(current)
        except:
            pass