import socket
import time
import sqlite3
import sys
import re

# Ensure UTF-8 encoding for proper terminal output
sys.stdout.reconfigure(encoding='utf-8')

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
    """
    Parses an RBN DX spot line into its components.
    Example line format:
    "DX de VE7CC-#:   28224.9  K5GJR/B        CW     5 dB  10 WPM  BEACON  2205Z"
    """

    # Regular expression to extract the needed fields
    match = re.search(r"DX de (\S+):\s+([\d.]+)\s+(\S+)\s+(\S+)\s+(\d+)\s+dB\s+.*\s+(\d{4}Z)", line)
    
    if match:
        spotting_station = match.group(1)  # e.g., "VE7CC-#"
        frequency = float(match.group(2))  # e.g., "28224.9"
        dx_callsign = match.group(3)       # e.g., "K5GJR/B"
        mode = match.group(4)              # e.g., "CW"
        snr = int(match.group(5))          # e.g., "5"
        timestamp = match.group(6)         # e.g., "2205Z"

        return {
            "spotting_station": spotting_station,
            "frequency": frequency,
            "dx_callsign": dx_callsign,
            "mode": mode,
            "snr": snr,
            "timestamp": timestamp
        }
    else:
        print(f"❌ Error parsing line: {line}")
        return None

import sqlite3

def save_to_database(data):
    """
    Saves the parsed spot data to the SQLite database.
    """
    try:
        conn = sqlite3.connect("data/hf_monitor.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO rbn_data (timestamp, spotting_station, dx_callsign, frequency, mode, snr)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["timestamp"], 
            data["spotting_station"], 
            data["dx_callsign"], 
            data["frequency"], 
            data["mode"], 
            data["snr"]
        ))

        conn.commit()
        conn.close()

        print(f"✅ Data saved: {data}")
    
    except sqlite3.Error as e:
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
