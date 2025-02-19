import socket
import time
import sqlite3
import sys

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
        sys.stdout.flush()  # Forces immediate print output
        with socket.create_connection((RBN_HOST, RBN_PORT), timeout=10) as s:
            time.sleep(2)  # Allow time for the server to respond

            # Send your callsign as the login
            s.sendall((CALLSIGN + "\n").encode("utf-8"))
            time.sleep(2)  # Give time for the server to respond
            
            print(f"✅ Successfully connected as {CALLSIGN}")
            sys.stdout.flush()  # Forces immediate print output

            # Start processing data
            process_rbn_data(s)
    except Exception as e:
        print(f"❌ Error connecting to RBN: {e}")
        sys.stdout.flush()  # Forces immediate print output

def process_rbn_data(socket_conn):
    """Read data from RBN and store it in SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rbn_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                callsign TEXT,
                frequency REAL,
                mode TEXT,
                snr INTEGER
            )
        """)
        conn.commit()

        while True:
            data = socket_conn.recv(4096).decode("utf-8", errors="ignore")
            if not data:
                break  # Connection closed

            # Process each line separately
            for line in data.split("\n"):
                line = line.strip()
                
                # ✅ Ignore welcome messages, user counts, or connection info
                if line.startswith("Please enter your call") or \
                   line.startswith("Hello,") or \
                   "Local users =" in line or \
                   "Current spot rate" in line or \
                   line.startswith("KQ4UFE de"):
                    continue  # Skip non-data lines
                
                parsed_data = parse_rbn_data(line)
                
                if parsed_data:
                    timestamp, callsign, frequency, mode, snr = parsed_data
                    if not is_duplicate_entry(DB_PATH, timestamp, callsign, frequency):
                        cursor.execute(
                            "INSERT INTO rbn_data (timestamp, callsign, frequency, mode, snr) VALUES (?, ?, ?, ?, ?)",
                            (timestamp, callsign, frequency, mode, snr),
                        )
                        conn.commit()
                        print(f"✅ {timestamp} | {callsign} | {frequency} MHz | {mode} | SNR: {snr}")
                        sys.stdout.flush()  # Forces immediate print output
                    else:
                        print(f"⏭️ Duplicate entry skipped: {callsign} on {frequency} MHz")
                        sys.stdout.flush()  # Forces immediate print output

    except Exception as e:
        print(f"❌ Error processing RBN data: {e}")
        sys.stdout.flush()  # Forces immediate print output
    finally:
        conn.close()

def parse_rbn_data(line):
    """
    Parses a single line of RBN data and extracts timestamp, callsign, frequency, mode, and SNR.
    Expected format:
    DX de <spotter>: <freq> <callsign> <mode> <snr> dB <speed> WPM <CQ/SPOT> <timestamp>
    """
    parts = line.split()

    if not line.startswith("DX de") or len(parts) < 7:
        return None  # Ignore invalid data

    try:
        spotter = parts[2].replace(":", "")  # Remove the colon
        frequency = float(parts[3])  # Frequency in MHz
        callsign = parts[4]  # Callsign of spotted station
        mode = parts[5]  # Mode (CW, FT8, etc.)
        snr = int(parts[6])  # Signal-to-noise ratio (SNR)
        utc_time = parts[-1]  # Timestamp from RBN data

        # Convert to proper timestamp format
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        return timestamp, callsign, frequency, mode, snr

    except (IndexError, ValueError) as e:
        print(f"⚠️ Error parsing line: {line} | {e}")
        sys.stdout.flush()  # Forces immediate print output
        return None

def is_duplicate_entry(db_path, timestamp, callsign, frequency):
    """Checks if an entry already exists in the database to prevent duplicates."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM rbn_data WHERE timestamp=? AND callsign=? AND frequency=?",
        (timestamp, callsign, frequency),
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

if __name__ == "__main__":
    connect_to_rbn()
