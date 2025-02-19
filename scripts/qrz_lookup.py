import requests
import xml.etree.ElementTree as ET
import time

# QRZ API Credentials (Replace with your actual credentials)
QRZ_LOGIN_URL = "https://xmldata.qrz.com/xml/current/"
QRZ_USERNAME = "kq4ufe"
QRZ_PASSWORD = 'ExceedRC1!'

# Global session storage
QRZ_SESSION_KEY = None
QRZ_SESSION_EXPIRY = 0

def get_qrz_session_key(force_renew=False):
    """Retrieve & cache QRZ session key, renewing only if expired."""
    global QRZ_SESSION_KEY, QRZ_SESSION_EXPIRY
    current_time = time.time()

    if QRZ_SESSION_KEY and current_time < QRZ_SESSION_EXPIRY and not force_renew:
        return QRZ_SESSION_KEY

    print("🔄 Fetching new QRZ session key...")
    params = {"username": QRZ_USERNAME, "password": QRZ_PASSWORD, "agent": "hf_monitor"}
    response = requests.get(QRZ_LOGIN_URL, params=params)

    if response.status_code == 200:
        root = ET.fromstring(response.content)
        key_element = root.find(".//Key")
        expiry_element = root.find(".//SubExp")

        if key_element is not None:
            QRZ_SESSION_KEY = key_element.text
            print(f"✅ QRZ Login Successful. Session Key: {QRZ_SESSION_KEY}")

            if expiry_element is not None:
                QRZ_SESSION_EXPIRY = time.mktime(time.strptime(expiry_element.text, "%a %b %d %H:%M:%S %Y"))
            
            return QRZ_SESSION_KEY
        else:
            print("❌ QRZ Login Failed: No session key found")
            QRZ_SESSION_KEY = None

    else:
        print(f"❌ QRZ Login Failed: HTTP {response.status_code}")

    return None

def qrz_call_lookup(callsign):
    """Look up callsign info from QRZ.com."""
    session_key = get_qrz_session_key()
    
    if not session_key:
        print("❌ QRZ Lookup Failed: No valid session key")
        return "Unknown", "Unknown"

    lookup_url = f"{QRZ_LOGIN_URL}?s={session_key}&callsign={callsign}"
    response = requests.get(lookup_url)

    if response.status_code == 200:
        root = ET.fromstring(response.content)
        state_element = root.find(".//state")
        country_element = root.find(".//country")

        return state_element.text if state_element is not None else "Unknown", \
               country_element.text if country_element is not None else "Unknown"
    
    if response.status_code in [403, 401]:
        print("🔄 QRZ session expired, renewing...")
        get_qrz_session_key(force_renew=True)

    return "Unknown", "Unknown"
