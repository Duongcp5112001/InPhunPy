# ChonChungTuController.py
import sys
import os
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from ConnectDB import get_oracle_connection, get_oracle_test_connection
import datetime

class ChungTuForm(QtWidgets.QWidget):
    selected_signal = pyqtSignal(dict)

    def __init__(self, parent_controller=None, machine_idx=1):
        super().__init__()
        self.parent_controller = parent_controller
        self.machine_idx = machine_idx
        uic.loadUi("ChonChungTu.ui", self)

        # === CỐ ĐỊNH KÍCH THƯỚC CỬA SỔ 1000px ===
        self.setFixedSize(1100, 600)
        
        # === SET WINDOW TITLE VÀ ICON ===
        self.setWindowTitle(f"Chọn Chứng Từ Cho Máy In {machine_idx}")
        self.set_window_icon()

        # === TỶ LỆ CỘT MỚI (6 cột - có STT) ===
        self.column_ratios = [7, 17, 17, 17, 24, 18]  # STT, GIỜ, BIỂN SỐ, SL, SẢN PHẨM, NGÀY

        self.setup_table()
        self.load_chung_tu_data()
        self.tableChungTu.doubleClicked.connect(self.on_row_double_clicked)

    def set_window_icon(self):
        """Thiết lập icon cho cửa sổ"""
        logo_path = "assets\logo_congty-Photoroom.png"
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        else:
            print(f"Không tìm thấy file logo: {logo_path}")

    def setup_table(self):
        table = self.tableChungTu
        table.setColumnCount(6)

        # Header
        headers = ["STT", "GIỜ CÂN XE", "BIỂN SỐ XE", "SL CẮT LỆNH", "SẢN PHẨM", "NGÀY CÂN XE"]
        for i, text in enumerate(headers):
            item = QtWidgets.QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(i, item)

        # Tăng chiều cao dòng cho phù hợp với font 19pt
        table.verticalHeader().setDefaultSectionSize(50)
        
        # Ẩn số thứ tự dòng
        table.verticalHeader().setVisible(False)

        # Resize mode cố định
        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)

        # Cập nhật chiều rộng cột
        self.update_column_widths()
        
        # Đặt kích thước bảng vừa khít với cửa sổ
        table.setFixedSize(1080, 580)
        
        # BẬT THEO DÕI CHUỘT VÀ KẾT NỐI SỰ KIỆN HOVER
        table.setMouseTracking(True)
        table.viewport().setMouseTracking(True)
        table.entered.connect(self.on_cell_hover)

    def on_cell_hover(self, index):
        """Khi hover vào ô bất kỳ - làm nổi bật cả dòng"""
        if index.isValid():
            # Đổi con trỏ chuột thành ngón tay
            self.tableChungTu.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Làm nổi bật cả dòng bằng cách chọn dòng đó
            self.tableChungTu.selectRow(index.row())

    def leaveEvent(self, event):
        """Khi chuột rời khỏi bảng"""
        self.tableChungTu.clearSelection()
        self.tableChungTu.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)

    def update_column_widths(self):
        table = self.tableChungTu
        total_width = 1080  # Vừa khít với bảng

        # Tính chiều rộng từng cột
        total_ratio = sum(self.column_ratios)

        for idx, ratio in enumerate(self.column_ratios):
            width = int(total_width * ratio / total_ratio)
            table.setColumnWidth(idx, width)

    def load_chung_tu_data(self):
        conn = get_oracle_connection()
        if not conn:
            QtWidgets.QMessageBox.critical(self, "Lỗi", "Không thể kết nối Oracle!")
            return
        try:
            cursor = conn.cursor()
            sql = """
            SELECT
                cml.documentno,
                cml.timenx,
                cml.transportno,
                cbp.ICP_Value,
                scm.value,
                mp.value,
                cml.totalamt,
                cml.todate
            FROM M_CommandLatching cml
            LEFT JOIN c_submarket scm ON cml.c_submarket_id = scm.c_submarket_id
            LEFT JOIN c_bpartner cbp ON cml.c_bpartner_id = cbp.c_bpartner_id
            LEFT JOIN m_product mp ON mp.m_product_id = cml.m_product1_id
            WHERE cml.ismanufacturer = 'Y'
                AND (cml.isbalance IS NULL OR cml.isbalance = 'N')
                AND cml.isleaved = 'N'
            ORDER BY cml.TimeNX ASC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            table = self.tableChungTu
            table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                # ĐÚNG: 8 cột → unpack 8 giá trị
                documentno, timenx, transportno, icp_value, scm_value, product_name, totalamt, todate = row

                # Dữ liệu hiển thị
                stt = str(row_idx + 1)
                gio_can = self.format_time(timenx)
                bien_so = (transportno or "").strip()
                sl_cat_lenh = str(totalamt) + " tấn" if totalamt else "0"
                san_pham = (product_name or "").strip()
                ngay_can = self.format_date(timenx)

                items = [stt, gio_can, bien_so, sl_cat_lenh, san_pham, ngay_can]
                for col_idx, value in enumerate(items):
                    item = QtWidgets.QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    table.setItem(row_idx, col_idx, item)

                # LƯU documentno vào UserRole
                table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, {
                    'documentno': documentno,
                    'timenx': timenx,
                    'transportno': transportno,
                    'icp_value': icp_value,
                    'scm_value': scm_value,
                    'product_name': product_name,
                    'totalamt': totalamt
                })
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Load dữ liệu thất bại:\n{e}")
        finally:
            cursor.close()
            conn.close()

    def format_time(self, dt):
        if not dt or not isinstance(dt, datetime.datetime):
            return ""
        return dt.strftime("%H:%M:%S")

    def format_date(self, dt):
        if not dt or not isinstance(dt, datetime.datetime):
            return ""
        return dt.strftime("%d/%m/%Y")

    def on_row_double_clicked(self, index):
        row = index.row()
        table = self.tableChungTu
        raw = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not raw:
            return

        # LẤY SỐ CHỨNG TỪ (documentno) - Đây là ID chính!
        documentno = raw.get('documentno') 
        if not documentno:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không tìm thấy số chứng từ!")
            return

        # Lấy ca làm việc từ UI chính
        ca_text = self.parent_controller.ui.LabelShift.text().strip() if self.parent_controller else "CA 1"
        ca_code = {"CA 1": "A", "CA 2": "B", "CA 3": "C"}.get(ca_text, "A")

        # Tạo mã in
        ma_in = (ca_code +
                (raw['transportno'] or "").replace("-", "") +
                (raw['icp_value'] or "") +
                (raw['scm_value'] or "") +
                self.format_date(raw['timenx']).replace("/", "")[-6:])

        # GỬI DỮ LIỆU KÈM documentno (số chứng từ)
        selected_data = {
            'documentno': str(documentno),
            'bien_so': (raw['transportno'] or "").strip(),
            'san_pham': (raw['product_name'] or "").strip(),
            'sl_cat_lenh': str(raw['totalamt']) if raw['totalamt'] else "0",
            'ma_in': ma_in
        }

        self.selected_signal.emit(selected_data)
        self.close()