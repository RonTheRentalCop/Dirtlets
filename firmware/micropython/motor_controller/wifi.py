import time

import network

import config


def connect_wifi():
    """Join the configured Wi-Fi network, or fall back to a temporary access point."""
    station = network.WLAN(network.STA_IF)
    station.active(True)
    if config.WIFI_SSID == "CHANGE_ME":
        station.active(False)
        access_point = network.WLAN(network.AP_IF)
        access_point.active(True)
        access_point.config(essid=config.SETUP_AP_SSID, authmode=network.AUTH_OPEN)
        print("Setup access point:", config.SETUP_AP_SSID)
        print("Connect the Mac to this Wi-Fi network")
        print("Board IP:", access_point.ifconfig()[0])
        return access_point

    if not station.isconnected():
        print("Connecting to Wi-Fi...")
        station.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while not station.isconnected():
            time.sleep_ms(250)
    print("Wi-Fi:", station.ifconfig())
    print("Board IP:", station.ifconfig()[0])
    return station
