from PyQt6 import uic
from PyQt6.QtWidgets import QDialog
from PyQt6.QtGui import QIcon
import os
import sqlite3
from ConnectDB import get_sqlite_printer_connection, get_sqlite_camera_connection


def get_printer_info(printer_id: int):
    """Lấy 1 record từ bảng printer theo id, trả về dict hoặc None"""
    try:
        conn = get_sqlite_printer_connection()
        if not conn:
            print(f"Không thể mở DB printer để lấy printer {printer_id}")
            return None
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT Name, IP, Position, Software, SW, PE, CE FROM printer WHERE id = ?", (printer_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            'Name': row['Name'],
            'IP': row['IP'],
            'Position': row['Position'],
            'Software': row['Software'],
            'SW': row['SW'],
            'PE': row['PE'],
            'CE': row['CE']
        }
    except Exception as e:
        print(f"Lỗi khi đọc printer info id={printer_id}: {e}")
        return None
    finally:
        try:
            cur.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass


def get_camera_info(camera_id: int):
    """Lấy 1 record từ bảng camera theo id, trả về dict hoặc None"""
    try:
        conn = get_sqlite_camera_connection()
        if not conn:
            print(f"Không thể mở DB camera để lấy camera {camera_id}")
            return None
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT Name, Position, IP, Connection, Rtsp FROM camera WHERE id = ?", (camera_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            'Name': row['Name'],
            'Position': row['Position'],
            'IP': row['IP'],
            'Connection': row['Connection'],
            'Rtsp': row['Rtsp']
        }
    except Exception as e:
        print(f"Lỗi khi đọc camera info id={camera_id}: {e}")
        return None
    finally:
        try:
            cur.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass


def show_chi_tiet_dialog(parent_window, machine_idx: int):
    """Mở dialog ChiTiet.ui và gán dữ liệu printer + camera theo machine_idx"""
    try:
        dlg = QDialog(parent_window)
        uic.loadUi('ChiTiet.ui', dlg)
        # Window title
        dlg.setWindowTitle(f"CHI TIẾT MÁY IN {machine_idx}")
        # Set header labels inside UI (if present) to include index
        try:
            if hasattr(dlg, 'labelHeader'):
                dlg.labelHeader.setText(f"THÔNG TIN MÁY IN {machine_idx}")
            if hasattr(dlg, 'labelHeaderCam'):
                dlg.labelHeaderCam.setText(f"THÔNG TIN CAMERA MÁY IN {machine_idx}")
        except Exception:
            pass

        # set icon if available
        try:
            logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo_congty-Photoroom.png')
            if os.path.exists(logo_path):
                dlg.setWindowIcon(QIcon(logo_path))
        except Exception:
            pass

        # Load printer info and populate fields (use names defined in ChiTiet.ui)
        p = get_printer_info(machine_idx)
        if p:
            try:
                if hasattr(dlg, 'txtTenMayIn'):
                    dlg.txtTenMayIn.setText(str(p.get('Name') or ''))
                if hasattr(dlg, 'txtIPMayIn'):
                    dlg.txtIPMayIn.setText(str(p.get('Position') or ''))
                if hasattr(dlg, 'txtIPPrinter'):
                    dlg.txtIPPrinter.setText(str(p.get('IP') or ''))
                if hasattr(dlg, 'txtPBPhanMem'):
                    dlg.txtPBPhanMem.setText(str(p.get('Software') or ''))
                if hasattr(dlg, 'txtSW'):
                    dlg.txtSW.setText(str(p.get('SW') or ''))
                if hasattr(dlg, 'txtPE'):
                    dlg.txtPE.setText(str(p.get('PE') or ''))
                if hasattr(dlg, 'txtCE'):
                    dlg.txtCE.setText(str(p.get('CE') or ''))
            except Exception:
                pass

        # Load camera info and populate fields
        c = get_camera_info(machine_idx)
        if c:
            try:
                if hasattr(dlg, 'txtTenCam'):
                    dlg.txtTenCam.setText(str(c.get('Name') or ''))
                if hasattr(dlg, 'txtViTri'):
                    dlg.txtViTri.setText(str(c.get('Position') or ''))
                if hasattr(dlg, 'txtIPCamera'):
                    dlg.txtIP.setText(str(c.get('IP') or ''))
                if hasattr(dlg, 'txtConnection'):
                    dlg.txtConnection.setText(str(c.get('Connection') or ''))
                if hasattr(dlg, 'txtRTSP'):
                    dlg.txtRTSP.setText(str(c.get('Rtsp') or ''))
            except Exception:
                pass

        dlg.exec()
    except Exception as e:
        print(f"Lỗi khi mở ChiTiet dialog: {e}")
