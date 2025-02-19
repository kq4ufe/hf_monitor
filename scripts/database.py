import sqlite3

DB_PATH = "hf_monitor.db"

def initialize_database():
    """Create database table if not exists."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rbn_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spotting_station TEXT,
                frequency REAL,
                dx_callsign TEXT,
                mode TEXT,
                snr INTEGER,
                timestamp TEXT
            )
        """)
        conn.commit()

def save_to_database(data):
    """Save parsed RBN spot to database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rbn_data (spotting_station, frequency, dx_callsign, mode, snr, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["spotting_station"], data["frequency"], data["dx_callsign"], 
            data["mode"], data["snr"], data["timestamp"]
        ))
        conn.commit()
