import socket
import time
import sqlite3
import sys
import re
import requests
import xml.etree.ElementTree as ET

#QRZ credentials
QRZ_USERNAME = "kq4ufe"
QRZ_PASSWORD = 'ExceedRC1!'
QRZ_Session = None

# Ensure UTF-8 encoding for proper terminal output
sys.stdout.reconfigure(encoding='utf-8')

def get_callsign_info(callsign):
    QRZ_USERNAME = "kq4ufe"
    QRZ_PASSWORD = 'ExceedRC1!'
    QRZ_SESSION = None

    if QRZ_SESSION is None:
        login_url = f"https://xmldata.qrz.com/xml/current/?username={QRZ_USERNAME};password={QRZ_PASSWORD}"
        response = requests.get(login_url)
        root = ElementTree.fromstring(response.content)
        QRZ_SESSION = root.find("Session").find("Key").text if root.find("Session") is not None else None
        if QRZ_SESSION is None:
            print("❌ Failed to obtain QRZ session key!")
            return None

    lookup_url = f"https://xmldata.qrz.com/xml/current/?s={QRZ_SESSION};callsign={callsign}"
    response = requests.get(lookup_url)
    print(f"🔹 QRZ API Response: {response.content.decode()}")  # Debugging line

    root = ElementTree.fromstring(response.content)
    callsign_info = root.find("Callsign")

    if callsign_info is None:
        print(f"❌ No Callsign Data Found for {callsign}")
        return None

    return {
        "callsign": callsign,
        "country": callsign_info.find("country").text if callsign_info.find("country") is not None else "Unknown",
        "grid": callsign_info.find("grid").text if callsign_info.find("grid") is not None else "Unknown"
    }

# RBN Telnet Server Information
RBN_HOST = "telnet.reversebeacon.net"
RBN_PORT = 7000
CALLSIGN = "kq4ufe"  # Replace with your own callsign

DB_PATH = "data/hf_monitor.db"  # Ensure this path matches your actual database location

def connect_to_rbn():
    """Connect to the RBN server and send the callsign."""
    try:
        print("📡 Connecting to Reverse Beacon Network...")
        sys.stdout.flush()  # Forces immediate print
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((RBN_HOST, RBN_PORT))
        s.sendall((CALLSIGN + "\n").encode())
        print(f"✅ Successfully connected as {CALLSIGN}")
        return s
    except Exception as e:
        print(f"❌ Error connecting to RBN: {e}")
        return None

def parse_spot_line(line):
    match = re.search(r'DX de (\S+):\s+([\d.]+)\s+(\S+)\s+(\S+)\s+(\d+)\s+dB\s+.*\s+(\d{4}Z)', line)
    if match:
        spotting_station = match.group(1)
        frequency = float(match.group(2))
        dx_callsign = match.group(3)
        mode = match.group(4)
        snr = int(match.group(5))
        timestamp = match.group(6)

        # Lookup grid squares
        spotting_grid = qrz_call_lookup(spotting_station)
        dx_grid = qrz_call_lookup(dx_callsign)

        return {
            'timestamp': timestamp,
            'spotting_station': spotting_station,
            'spotting_grid': spotting_grid,
            'dx_callsign': dx_callsign,
            'dx_grid': dx_grid,
            'frequency': frequency,
            'mode': mode,
            'snr': snr
        }
    else:
        print(f"❌ Error parsing line: {line}")
        return None

def save_to_database(spot):
    try:
        conn = sqlite3.connect('data/hf_monitor.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rbn_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                spotting_station TEXT,
                spotting_grid TEXT,
                dx_callsign TEXT,
                dx_grid TEXT,
                frequency REAL,
                mode TEXT,
                snr INTEGER
            )
        ''')
        cursor.execute('''
            INSERT INTO rbn_data (timestamp, spotting_station, spotting_grid, dx_callsign, dx_grid, frequency, mode, snr)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            spot['timestamp'], spot['spotting_station'], spot['spotting_grid'],
            spot['dx_callsign'], spot['dx_grid'], spot['frequency'],
            spot['mode'], spot['snr']
        ))
        conn.commit()
        conn.close()
        print(f"✅ Data saved: {spot}")
    except Exception as e:
        print(f"❌ Error saving to database: {e}")

def main():
    socket_conn = connect_to_rbn()
    if not socket_conn:
        return

    try:
        buffer = ""
        while True:
            data = socket_conn.recv(4096).decode('utf-8', errors='ignore')
            if not data:
                break
            buffer += data
            lines = buffer.split('\n')
            buffer = lines.pop()  # The last line may be incomplete, keep it in buffer

            for line in lines:
                print(f"🔹 Raw Data: {line}")  # Debugging: print each received line
                spot = parse_spot_line(line)
                if spot:
                    save_to_database(spot)
    except KeyboardInterrupt:
        print("🛑 Interrupted by user.")
    except Exception as e:
        print(f"❌ Error during RBN data processing: {e}")
    finally:
        socket_conn.close()
        print("🔌 Connection closed.")

if __name__ == "__main__":
    main()
