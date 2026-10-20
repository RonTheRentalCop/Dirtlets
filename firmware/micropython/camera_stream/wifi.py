import time

import network

import config
import wifi_secrets


def connect_wifi(timeout_s=20):
    try:
        network.hostname(config.HOSTNAME)
    except AttributeError:
        pass
    station = network.WLAN(network.STA_IF)
    station.active(True)
    try:
        station.config(pm=station.PM_NONE)
    except (AttributeError, ValueError):
        pass

    if not station.isconnected():
        print("Connecting to Wi-Fi...")
        station.connect(wifi_secrets.WIFI_SSID, wifi_secrets.WIFI_PASSWORD)
        started = time.time()
        while not station.isconnected():
            if time.time() - started > timeout_s:
                print("Wi-Fi failed, restarting")
                import machine
                machine.reset()
            time.sleep_ms(250)
    print("Wi-Fi:", station.ifconfig())
    print("Board IP:", station.ifconfig()[0])
    return station
