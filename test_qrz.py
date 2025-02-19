import requests

QRZ_USERNAME = "kq4ufe"
QRZ_PASSWORD = "ExceedRC1!"

# Request QRZ session key
url = f"https://xmldata.qrz.com/xml/current/?username={QRZ_USERNAME};password={QRZ_PASSWORD};agent=hf_monitor"
response = requests.get(url)

# Print response to debug
print(response.text)
