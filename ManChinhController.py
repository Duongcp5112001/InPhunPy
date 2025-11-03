# controller.py
from PyQt6.QtCore import QTimer, QDateTime
from PyQt6.QtWidgets import QMenu, QWidgetAction
from PyQt5 import QtCore
from ChuyenMayInController import MaySelectorWidget
from ConnectOracle import get_oracle_connection

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
        widget = MaySelectorWidget()
        choices = [i for i in range(1, 5) if i != current_idx]

        widget.radioMay1.setText(f"Máy In {choices[0]}")
        widget.radioMay2.setText(f"Máy In {choices[1]}")
        widget.radioMay3.setText(f"Máy In {choices[2]}")

        menu = QMenu(self.window)
        action = QWidgetAction(menu)
        action.setDefaultWidget(widget)
        menu.addAction(action)
        menu.setFixedWidth(190)

        # TÍNH VỊ TRÍ HIỆN TRÊN NÚT
        button_rect = button.rect()
        pos = button.mapToGlobal(button_rect.topLeft())  # Lấy góc trên trái
        pos.setY(pos.y() - menu.sizeHint().height() + 45)  # DỊCH LÊN 50PX + CHIỀU CAO MENU

        # ĐẢM BẢO KHÔNG ÂM (ra ngoài màn hình trên)
        screen = self.window.screen().availableGeometry()
        if pos.y() < screen.top():
            pos.setY(screen.top() + 10)  # Hiện sát đỉnh màn hình

        # HIỆN MENU BÊN PHẢI / TRÁI
        if current_idx == 4:
            pos.setX(pos.x() + button.width() - menu.width() - 170)  # Nút 4 → bên trái
        else:
            pos.setX(pos.x() + button.width())  # Các nút → bên phải

        menu.exec(pos)

        if widget.selected:
            print(f"Máy In {current_idx} → {widget.selected}")    
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
        print(f"Refresh dữ liệu máy in {idx}")
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
    #
    


    