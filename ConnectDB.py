# db.py
import oracledb
import sqlite3
oracledb.init_oracle_client(lib_dir=r"C:\Users\duongnh48\instantclient-basic-windows.x64-19.28.0.0.0dbru\instantclient_19_28")

def get_oracle_connection():
    """
    Trả về connection đến Oracle DB
    Thay đổi: username, password, dsn theo DB của bạn
    """
    try:
        return oracledb.connect(
            user="xmcp",
            password="Admin123",
            dsn="10.0.0.10:1521/orcl.ximangcampha.net"
        )
    except oracledb.Error as e:
        print("Lỗi kết nối Oracle:", e)
        return None

def get_oracle_test_connection():
    """
    Trả về connection đến Oracle DB
    Thay đổi: username, password, dsn theo DB của bạn
    """
    try:
        return oracledb.connect(
            user="test_giathanh",
            password="Admin123",
            dsn="10.0.0.11:1521/orcl.ximangcampha.net"
        )
    except oracledb.Error as e:
        print("Lỗi kết nối Oracle:", e)
        return None

def get_sqlite_printer_connection():
    """
    Trả về connection đến SQLite DB cho máy in
    Thay đổi: đường dẫn file DB theo máy của bạn
    """
    try:
        return sqlite3.connect(r"X:\printer.db")
    except sqlite3.Error as e:
        print("Lỗi kết nối SQLite:", e)
        return None
    
def get_sqlite_camera_connection():
    """
    Trả về connection đến SQLite DB cho máy in
    Thay đổi: đường dẫn file DB theo máy của bạn
    """
    try:
        return sqlite3.connect(r"X:\camera.db")
    except sqlite3.Error as e:
        print("Lỗi kết nối SQLite:", e)
        return None
    
def get_sqlite_pause_print_connection():
    """
    Trả về connection đến SQLite DB cho máy in
    Thay đổi: đường dẫn file DB theo máy của bạn
    """
    try:
        return sqlite3.connect(r"X:\pause_print_information.db")
    except sqlite3.Error as e:
        print("Lỗi kết nối SQLite:", e)
        return None
    
def get_sqlite_log_connection():
    """
    Trả về connection đến SQLite DB cho máy in
    Thay đổi: đường dẫn file DB theo máy của bạn
    """
    try:
        return sqlite3.connect(r"X:\log.db")
    except sqlite3.Error as e:
        print("Lỗi kết nối SQLite:", e)
        return None