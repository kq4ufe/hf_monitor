import socket
import sqlite3
import time
import re
import xml.etree.ElementTree as ET
import requests

# QRZ Credentials
QRZ_USERNAME = "your_qrz_username"
QRZ_PASSWORD = "your_qrz_password"
QRZ_SESSION_KEY = None  # This will be set after login

# Reverse Beacon Network Configuration
RBN_HOST = "telnet.reversebeacon.net"
RBN_PORT = 7000
CALLSIGN = "KQ4UFE"

# Database setup
DB_PATH = "data/hf_monitor.db"

def connect_to_qrz():
    """Authenticate with QRZ and retrieve a session key."""
    global QRZ_SESSION_KEY
    login_url = f"https://xmldata.qrz.com/xml/current/?username={QRZ_USERNAME};password={QRZ_PASSWORD}"
    response = requests.get(login_url)

    if response.status_code == 200:
        root = ET.fromstring(response.text)
        key_element = root.find(".//Key")
        if key_element is not None:
            QRZ_SESSION_KEY = key_element.text
            print(f"✅ QRZ Session Key Retrieved: {QRZ_SESSION_KEY}")
        else:
            print("❌ QRZ Login Failed: No session key found")
    else:
        print("❌ QRZ Login Failed: Invalid response from QRZ")

def qrz_call_lookup(callsign):
    """Retrieve location information for a callsign from QRZ.com."""
    if QRZ_SESSION_KEY is None:
        connect_to_qrz()
        if QRZ_SESSION_KEY is None:
            return None  # Return None if QRZ login failed

    query_url = f"https://xmldata.qrz.com/xml/current/?s={QRZ_SESSION_KEY};callsign={callsign}"
    response = requests.get(query_url)

    if response.status_code == 200:
        root = ET.fromstring(response.text)
        state = root.find(".//state")
        country = root.find(".//country")
        return {
            "callsign": callsign,
            "state": state.text if state is not None else "Unknown",
            "country": country.text if country is not None else "Unknown",
        }
    else:
        print(f"❌ QRZ Lookup Failed for {callsign}")
        return None

def parse_rbn_line(line):
    """Parse RBN telnet lines into structured data."""
    try:
        parts = re.split(r'\s+', line.strip())
        if parts[0] != "DX":
            raise ValueError("Not a valid DX spot line")

        spotting_station = parts[2]
        frequency = float(parts[3])
        dx_callsign = parts[4]
        mode = parts[5]
        snr = int(parts[6])
        timestamp = parts[-1]  # Last value in the line

        # Lookup locations for both stations
        spotting_info = qrz_call_lookup(spotting_station)
        dx_info = qrz_call_lookup(dx_callsign)

        return {
            "spotting_station": spotting_station,
            "spotting_state": spotting_info["state"] if spotting_info else "Unknown",
            "spotting_country": spotting_info["country"] if spotting_info else "Unknown",
            "frequency": frequency,
            "dx_callsign": dx_callsign,
            "dx_state": dx_info["state"] if dx_info else "Unknown",
            "dx_country": dx_info["country"] if dx_info else "Unknown",
            "mode": mode,
            "snr": snr,
            "timestamp": timestamp
        }
    except Exception as e:
        print(f"❌ Error parsing line: {line.strip()} | {e}")
        return None

def save_to_database(data):
    """Save parsed RBN data to the SQLite database."""
    if data is None:
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO rbn_data 
            (spotting_station, spotting_state, spotting_country, frequency, dx_callsign, dx_state, dx_country, mode, snr, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["spotting_station"], data["spotting_state"], data["spotting_country"],
                data["frequency"], data["dx_callsign"], data["dx_state"], data["dx_country"],
                data["mode"], data["snr"], data["timestamp"]
            )
        )
        conn.commit()
        conn.close()
        print(f"✅ Data saved: {data}")
    except Exception as e:
        print(f"❌ Error saving to database: {e}")

def connect_to_rbn():
    """Connect to RBN and continuously process data."""
    while True:
        try:
            print("📡 Connecting to Reverse Beacon Network...")
            sock = socket.create_connection((RBN_HOST, RBN_PORT))
            sock.sendall(f"{CALLSIGN}\n".encode())

            with sock.makefile() as rbn_stream:
                for line in rbn_stream:
                    line = line.strip()
                    print(f"🔹 Raw Data: {line}")

                    parsed_data = parse_rbn_line(line)
                    if parsed_data:
                        save_to_database(parsed_data)

        except Exception as e:
            print(f"❌ RBN Connection Error: {e}")
            time.sleep(5)  # Wait before reconnecting

if __name__ == "__main__":
    connect_to_rbn()
