# utils.py
import os
import sys

def resource_path(relative_path):
    """Lấy đường dẫn đúng cho file .ui, .png, .jpg khi chạy .exe"""
    try:
        # PyInstaller tạo thư mục tạm
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)