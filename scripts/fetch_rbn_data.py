import socket
from rbn_parser import parse_rbn_line
from qrz_lookup import qrz_call_lookup
from database import save_to_database, initialize_database

# RBN Connection Details
RBN_HOST = "ve7cc.net"
RBN_PORT = 23
CALLSIGN = "kq4ufe"

def connect_to_rbn():
    global rbn_socket #ensure its accessible everywhere

    print("📡 Connecting to RBN...")
    rbn_socket = socket.create_connection(("dxc.ve7cc.net", 23))  # Ensure correct host/port
    rbn_stream = rbn_socket.makefile('r')

    """Connects to RBN, fetches spots, parses & stores them."""
    with socket.create_connection((RBN_HOST, RBN_PORT)) as sock:
        print(f"✅ Connected to RBN as {CALLSIGN}")
        sock.sendall(f"SET/CALL {CALLSIGN}\n".encode())
    # Send initial command to enable DX spots and disable unnecessary messages
    rbn_socket.sendall(b"SET/SKIMMER\n")  # Enable Skimmer spots
    rbn_socket.sendall(b"SET/NOBEACON\n")  # Disable beacons if not needed
    rbn_socket.sendall(b"SET/DX\n")  # Ensure we receive DX spots

            with sock.makefile() as rbn_stream:
            for line in rbn_stream:
                data = parse_rbn_line(line)
                if data:
                    print(f"✅ Data saved: {data}")
                    spotting_state, spotting_country = qrz_call_lookup(data["dx_callsign"])
                    data["dx_state"] = spotting_state
                    data["dx_country"] = spotting_country
                    save_to_database(data)
                else:
                    print(f"❌ Ignored line: {line.strip()} | Not a valid DX spot")

if __name__ == "__main__":
    initialize_database()
    connect_to_rbn()

def parse_rbn_line(line):
    """
    Parses an RBN data line, extracting relevant information.
    Filters out system messages and non-DX lines.
    """

    # Ignore system messages and empty lines
    if not line.strip() or "Please enter your call:" in line or "Connected to" in line:
        return None

    # Regular expression to match DX spots
    dx_pattern = re.compile(
        r"DX de (\S+):\s+(\d+\.\d+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\d{4}Z)"
    )

    match = dx_pattern.search(line)
    if match:
        return {
            "spotting_station": match.group(1),
            "frequency": float(match.group(2)),
            "dx_callsign": match.group(3),
            "mode": match.group(4),
            "snr": int(match.group(5)),
            "speed": int(match.group(6)),  # WPM or BPS
            "comment": match.group(7),  # CQ, BEACON, etc.
            "timestamp": match.group(8),
        }
    
    # If the line does not match a valid DX spot, ignore it
    return None
