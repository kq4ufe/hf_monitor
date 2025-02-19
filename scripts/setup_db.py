import sqlite3

# Define the database file location
DB_PATH = "data/hf_monitor.db"

# Create the database schema
def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table for RBN data
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

    # Table for Solar Weather data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solar_weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        k_index INTEGER,
        estimated_kp REAL,
        source TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Database setup complete.")

# Run the function
if __name__ == "__main__":
    setup_database()
