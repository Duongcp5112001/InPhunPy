# db.py
import os
import sys
import sqlite3

# When bundled with PyInstaller (one-file), resources are extracted to sys._MEIPASS
base_dir = getattr(sys, "_MEIPASS", os.path.dirname(__file__))

# Candidate locations for Instant Client inside repo or extracted bundle
candidates = [
    os.path.join(base_dir, "instantclient", "instantclient_19_28"),
    os.path.join(base_dir, "instantclient_19_28"),
    os.path.join(base_dir, "instantclient"),
]

# Setup startup log file so GUI (no console) runs still produce diagnostic output
try:
    # When bundled/frozen, write log next to the exe so double-click runs produce the file
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = os.environ.get('TEMP', os.path.dirname(__file__))
    temp_log = os.path.join(log_dir, 'InPhunApp_startup.log')

    def _log_startup(msg):
        try:
            with open(temp_log, 'a', encoding='utf-8') as lf:
                lf.write(f"[{__name__}] {msg}\n")
        except Exception:
            pass
    _log_startup(f"Application base_dir={base_dir}")
    _log_startup(f"Candidate instantclient paths={candidates}")
except Exception:
    pass

lib_dir = next((p for p in candidates if os.path.isdir(p)), None)

if lib_dir:
    # Prepend to PATH so Windows loader can find Oracle DLLs when importing python-oracledb
    os.environ["PATH"] = lib_dir + os.pathsep + os.environ.get("PATH", "")
    _log_startup(f"Instant Client library dir set to: {lib_dir}")
else:
    _log_startup("Instant Client folder not found in bundle or repo; falling back (thin mode possible)")

try:
    import importlib, traceback
    importlib.invalidate_caches()
    import oracledb
    if lib_dir:
        try:
            oracledb.init_oracle_client(lib_dir=lib_dir)
            _log_startup("oracledb.init_oracle_client succeeded")
            # list files in lib_dir for debugging
            try:
                files = os.listdir(lib_dir)
                _log_startup(f"instantclient files: {files}")
            except Exception as e:
                _log_startup(f"listing instantclient failed: {e}")
        except Exception as e:
            # Could already be initialized or fail; log and continue
            _log_startup(f"Warning: init_oracle_client failed or already initialized: {e}")
    else:
        _log_startup("oracledb loaded; running in thin mode unless init_oracle_client is called")
except Exception as e:
    try:
        import traceback
        _log_startup(f"Failed to import oracledb: {e}")
        _log_startup(traceback.format_exc())
    except Exception:
        pass
    oracledb = None

# --- Database helper functions ---

def get_oracle_connection():
    """
    Trả về connection đến Oracle DB
    Thay đổi: username, password, dsn theo DB của bạn
    """
    if oracledb is None:
        print("[ConnectDB] oracledb module not available")
        return None

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
    if oracledb is None:
        print("[ConnectDB] oracledb module not available")
        return None

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