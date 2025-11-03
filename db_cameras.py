import sqlite3
import os

def init_camera_database():
    """Khởi tạo database và dữ liệu mẫu cho camera"""
    db_path = "camera.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tạo bảng cameras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY,
            machine_number INTEGER UNIQUE,
            ip_address TEXT NOT NULL,
            rtsp_url TEXT NOT NULL,
            status INTEGER DEFAULT 1
        )
    """)
    
    # Thêm dữ liệu mẫu cho 4 máy in
    cameras_data = [
        (1, '192.168.52.116', 'rtsp://admin:Campha%402022@117.4.48.122:5555/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif', 1),
        (2, '192.168.52.117', 'rtsp://admin:Campha%402022@117.4.48.122:5556/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif', 1),
        (3, '192.168.52.118', 'rtsp://admin:Campha%402022@117.4.48.122:5557/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif', 1),
        (4, '192.168.52.119', 'tsp://admin:Campha%402022@117.4.48.122:5558/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif', 1)
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO cameras (machine_number, ip_address, rtsp_url, status)
        VALUES (?, ?, ?, ?)
    """, cameras_data)
    
    conn.commit()
    conn.close()
    print("Đã khởi tạo database camera thành công!")

if __name__ == "__main__":
    init_camera_database()