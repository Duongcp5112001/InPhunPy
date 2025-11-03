# ChuyenMayInController.py
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt

class MaySelectorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ChuyenMayIn.ui", self)  # Đảm bảo file đúng tên
        self.selected = None

        # Kết nối radio
        self.radioMay1.toggled.connect(lambda c: self.select_if_checked(self.radioMay1, c))
        self.radioMay2.toggled.connect(lambda c: self.select_if_checked(self.radioMay2, c))
        self.radioMay3.toggled.connect(lambda c: self.select_if_checked(self.radioMay3, c))

    def select_if_checked(self, radio, checked):
        if checked:
            self.selected = radio.text()
            menu = self.parent()
            if isinstance(menu, QMenu):
                menu.close()