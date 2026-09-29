# Citation: AI-assisted code generation - Claude (Anthropic, 2026).
# AI help was limited to small scripting mistakes and troubleshooting
# while fixing shorted electronics. The code and design are my own.

from machine import Pin
from wifi import connect_wifi
from motor import MotorController
from udp_control import CommandReceiver
import config


class StatusLight:
    def __init__(self):
        self.pin = None
        if config.STATUS_LED_PIN is not None:
            self.pin = Pin(config.STATUS_LED_PIN, Pin.OUT, value=0)

    def on(self):
        if self.pin:
            self.pin.value(1 if config.STATUS_LED_ACTIVE_HIGH else 0)

    def off(self):
        if self.pin:
            self.pin.value(0 if config.STATUS_LED_ACTIVE_HIGH else 1)


connect_wifi()
motors = MotorController()
light = StatusLight()
receiver = CommandReceiver(motors, light)
print("Rover ready, UDP port", config.UDP_PORT)

try:
    while True:
        receiver.poll()
        receiver.enforce_timeout()
except KeyboardInterrupt:
    pass
finally:
    receiver.close()
    motors.deinit()
    print("Rover stopped")