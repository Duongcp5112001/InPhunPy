from PyQt6 import uic
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import pyqtSignal

class BaoRachVoForm(QDialog):
    confirmed = pyqtSignal(int, str, str, int)  # (hanh_dong, bao_rach, bao_thua, printer_id)

    def __init__(self, printer_id):
        super().__init__()
        self.printer_id = printer_id
        uic.loadUi('BaoRachVoForm.ui', self)

        # Cập nhật tiêu đề với số máy
        self.headerLabel.setText(f"XÁC NHẬN KẾT THÚC IN - Máy in {printer_id}")

        # Mặc định radio
        self.radioKetThuc.setChecked(True)

        # Kết nối nút
        self.btnXacNhan.clicked.connect(self.xac_nhan)

    def xac_nhan(self):
        bao_rach = self.txtBaoRach.text().strip() or "0"
        bao_thua = self.txtBaoThua.text().strip() or "0"
        hanh_dong = 1 if self.radioKetThuc.isChecked() else 2
        try:
            self.confirmed.emit(hanh_dong, bao_rach, bao_thua, self.printer_id)
        except Exception:
            pass
        self.accept()