# PrinterClient.py
import socket
from PyQt6.QtCore import QThread, pyqtSignal

class PrinterClient(QThread):
    data_received = pyqtSignal(int, str)  
    disconnected = pyqtSignal(int)        

    def __init__(self, idx, ip, port=9100):
        super().__init__()
        self.idx = idx
        self.ip = ip
        self.port = port
        self.socket = None
        self.running = False
        self.buffer = ""

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(3)
            self.socket.connect((self.ip, self.port))
            print(f"[MÁY {self.idx}] Kết nối thành công: {self.ip}:{self.port}")
            return True
        except Exception as e:
            print(f"[MÁY {self.idx}] Lỗi kết nối: {e}")
            return False

    def send(self, command):
        if not self.socket:
            return False
        try:
            if command == "GA":
                cmd = b'\x02GA\x03'
            elif command == "E":
                cmd = b'\x02E\x03'
            else:
                cmd = command.encode('utf-8')
            self.socket.send(cmd)
            return True
        except Exception as e:
            print(f"[GỬI LỆNH] Lỗi: {e}")
            return False

    def run(self):
        self.running = True
        while self.running and self.socket:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                text = data.decode('utf-8', errors='ignore')
                self.buffer += text
                self.process_buffer()
            except socket.timeout:
                continue
            except:
                break
        self.cleanup()
        self.disconnected.emit(self.idx)

    def process_buffer(self):
        while '\x03' in self.buffer:
            packet, self.buffer = self.buffer.split('\x03', 1)
            if packet.startswith('\x02'):
                packet = packet[1:]
            if packet:
                self.data_received.emit(self.idx, packet)

    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.wait()

    def cleanup(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None

    def send_raw(self, data):
        """Gửi dữ liệu thô (bytes)"""
        if not self.socket:
            return False
        try:
            self.socket.send(data)
            return True
        except:
            return False