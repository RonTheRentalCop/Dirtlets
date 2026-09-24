from machine import Pin

import config


class StatusLight:
    def __init__(self):
        self._pin = None
        self._active_high = config.STATUS_LED_ACTIVE_HIGH
        if config.STATUS_LED_PIN is not None:
            self._pin = Pin(config.STATUS_LED_PIN, Pin.OUT)
            self.off()

    def _write(self, active):
        if self._pin is None:
            return
        level = 1 if active == self._active_high else 0
        self._pin.value(level)

    def on(self):
        self._write(True)

    def off(self):
        self._write(False)

    def toggle(self):
        if self._pin is not None:
            self._pin.value(0 if self._pin.value() else 1)