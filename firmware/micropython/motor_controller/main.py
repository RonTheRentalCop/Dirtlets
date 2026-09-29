import time

import config
from lights import StatusLight
from motor import MotorController
from udp_control import CommandReceiver
from wifi import connect_wifi


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
