# db.py
import oracledb
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