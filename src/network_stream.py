import socket
import time
HOST="127.0.0.1"
PORT=6006

class PSRRStreamer:
    def __init__(self):
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def send_row(self, row):
        packet=(f"{row['frequency_hz']},"
            f"{row['psrr_db']},"
            f"{row['vin_ac_v']},"
            f"{row['vout_ac_v']},"
            f"{row['severity']}" )
        self.sock.sendto(packet.encode(), (HOST,PORT))
    def close(self):
        self.sock.close()
