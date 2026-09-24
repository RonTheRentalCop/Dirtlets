import time

import config
import network
from lights import StatusLight
from motor import MotorController
from udp_control import CommandReceiver


def connect_wifi():
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
    return station


def main():
    status_light = StatusLight()
    motor_controller = MotorController()
    connect_wifi()
    command_receiver = CommandReceiver(motor_controller, status_light)
    print("Ready. UDP port:", config.UDP_PORT)
    print("Commands: STOP or DRIVE <left> <right>")

    try:
        while True:
            command_receiver.poll()
            command_receiver.enforce_timeout()
            time.sleep_ms(10)
    except KeyboardInterrupt:
        print("Stopping motors")
    finally:
        command_receiver.close()
        status_light.off()


main()
