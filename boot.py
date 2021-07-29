from network import WLAN
import machine
import time
import pycom
import credentials

# Turn off heartbeat to make onboard LED adressable
pycom.heartbeat(False)

# Build up WiFi connection
pycom.pybytes_on_boot(False)

wlan = WLAN(mode=WLAN.STA)
wlan.antenna(WLAN.INT_ANT)
wlan.connect(credentials.wifi_ssid, auth=(WLAN.WPA2, credentials.wifi_password), timeout=5000) # SSID and password are configured in credentials.py

while not wlan.isconnected ():
    machine.idle()
if wlan.isconnected() == True:
    print()
    print("Connected to Wifi\n")
