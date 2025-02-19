import socket
from rbn_parser import parse_rbn_line
from qrz_lookup import qrz_call_lookup
from database import save_to_database, initialize_database

# RBN Connection Details
RBN_HOST = "ve7cc.net"
RBN_PORT = 23
CALLSIGN = "kq4ufe"

def connect_to_rbn():
    """Connects to RBN, fetches spots, parses & stores them."""
    with socket.create_connection((RBN_HOST, RBN_PORT)) as sock:
        print(f"✅ Connected to RBN as {CALLSIGN}")
        sock.sendall(f"SET/CALL {CALLSIGN}\n".encode())

        with sock.makefile() as rbn_stream:
            for line in rbn_stream:
                data = parse_rbn_line(line)
                if data:
                    spotting_state, spotting_country = qrz_call_lookup(data["dx_callsign"])
                    data["dx_state"] = spotting_state
                    data["dx_country"] = spotting_country
                    save_to_database(data)

if __name__ == "__main__":
    initialize_database()
    connect_to_rbn()
