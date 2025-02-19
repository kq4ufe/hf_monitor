import re

def parse_rbn_line(line):
    """Extract structured data from raw RBN lines."""
    match = re.search(r"DX de (\S+):\s+([\d\.]+)\s+(\S+)\s+(\S+)\s+([\d-]+)\s+\S+\s+\S+\s+(\d+Z)", line)
    if not match:
        print(f"❌ Error parsing line: {line} | Not a valid DX spot line")
        return None

    return {
        "spotting_station": match.group(1),
        "frequency": float(match.group(2)),
        "dx_callsign": match.group(3),
        "mode": match.group(4),
        "snr": int(match.group(5)),
        "timestamp": match.group(6)
    }
