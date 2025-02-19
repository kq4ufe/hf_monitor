import requests
import sqlite3
from datetime import datetime, timezone

# ✅ Correct API URL
SOLAR_WEATHER_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
DB_PATH = "data/hf_monitor.db"

def fetch_solar_weather():
    """Fetch solar weather data from NOAA and store it in the database."""
    try:
        print("☀️ Fetching Solar Weather data...")
        response = requests.get(SOLAR_WEATHER_URL, timeout=10)
        response.raise_for_status()
        
        data = response.json()

        if not data:
            raise ValueError("❌ Received empty response from NOAA API")

        # Extract the latest entry
        latest_entry = data[-1]  # Get the most recent data point

        timestamp = latest_entry["time_tag"]
        k_index = int(latest_entry["kp_index"])  # Correct key name
        estimated_kp = float(latest_entry["estimated_kp"])  # Correct key name
        source = "NOAA SWPC"

        # Store in the database
        save_to_db(timestamp, k_index, estimated_kp, source)

    except Exception as e:
        print("❌ Error fetching solar weather data:", e)

def save_to_db(timestamp, k_index, estimated_kp, source):
    """Save solar weather data to SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure the table exists
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

    # Insert the data
    cursor.execute(
        "INSERT INTO solar_weather (timestamp, k_index, estimated_kp, source) VALUES (?, ?, ?, ?)",
        (timestamp, k_index, estimated_kp, source),
    )
    conn.commit()
    conn.close()
    
    print(f"✅ Solar weather data stored: {timestamp} | K-index: {k_index} | Estimated Kp: {estimated_kp}")

if __name__ == "__main__":
    fetch_solar_weather()
