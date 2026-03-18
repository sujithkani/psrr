import socket
import time
HOST="100.64.20.32" #Receiver Address
PORT=6006

class PSRRStreamer:
    def __init__(self, host="127.0.0.1", port=6006):
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host=host
        self.port=port
    """
    def send_row(self, row):
        packet=(f"{row['frequency_hz']},"
            f"{row['psrr_db']},"
            f"{row['vin_ac_v']},"
            f"{row['vout_ac_v']},"
            f"{row['severity']}" )
        self.sock.sendto(packet.encode(), (HOST,PORT))
    """
    def send_row(self, row, idx=None, total=None):  
        if idx is not None and total is not None:
            prefix=f"{idx+1}/{total},"
        else:
            prefix=""
        packet=(
            prefix +
            f"{row['frequency_hz']},"
            f"{row['psrr_db']},"
            f"{row['vin_ac_v']},"
            f"{row['vout_ac_v']},"
            f"{row['severity']}"
        )
        try:
            self.sock.sendto(packet.encode(), (self.host, self.port))
        except Exception as e:
            print("UDP ERROR:", e)

    def close(self):
        self.sock.close()
