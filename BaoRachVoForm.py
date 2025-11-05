from PyQt6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QRadioButton,
    QPushButton, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal

class BaoRachVoForm(QDialog):
    confirmed = pyqtSignal(int, str, str, int)  # (hanh_dong, bao_rach, bao_thua, printer_id)

    def __init__(self, printer_id):
        super().__init__()
        self.printer_id = printer_id
        self.hanh_dong = 1  # Mặc định: tắt in
        self.bao_rach = "0"
        self.bao_thua = "0"
        self.setWindowTitle(f"Máy {printer_id} - Báo Rách / Thừa")
        self.setFixedSize(380, 220)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"<b>MÁY {self.printer_id}</b>"))

        # Bao rách
        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Bao rách:"))
        self.txt_bao_rach = QLineEdit("0")
        self.txt_bao_rach.setFixedWidth(80)
        r_layout.addWidget(self.txt_bao_rach)
        layout.addLayout(r_layout)

        # Bao thừa
        t_layout = QHBoxLayout()
        t_layout.addWidget(QLabel("Bao thừa:"))
        self.txt_bao_thua = QLineEdit("0")
        self.txt_bao_thua.setFixedWidth(80)
        t_layout.addWidget(self.txt_bao_thua)
        layout.addLayout(t_layout)

        # Hành động
        self.radio_tat_in = QRadioButton("Tắt in hoàn toàn")
        self.radio_tam_dung = QRadioButton("Tạm dừng (giữ dữ liệu)")
        self.radio_tat_in.setChecked(True)
        layout.addWidget(self.radio_tat_in)
        layout.addWidget(self.radio_tam_dung)

        # Nút
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Xác nhận")
        btn_cancel = QPushButton("Hủy")
        btn_ok.clicked.connect(self.xac_nhan)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def xac_nhan(self):
        self.bao_rach = self.txt_bao_rach.text().strip() or "0"
        self.bao_thua = self.txt_bao_thua.text().strip() or "0"
        self.hanh_dong = 1 if self.radio_tat_in.isChecked() else 2
        self.confirmed.emit(self.hanh_dong, self.bao_rach, self.bao_thua, self.printer_id)
        self.accept()