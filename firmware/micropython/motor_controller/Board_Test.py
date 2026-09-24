import time

from machine import Pin

import config


light_pins = [
	Pin(pin_number, Pin.OUT)
	for pin_number in config.TEST_LIGHT_PINS
	if pin_number is not None
]


def set_all(active):
	for light_pin in light_pins:
		if config.STATUS_LED_ACTIVE_HIGH:
			light_pin.value(1 if active else 0)
		else:
			light_pin.value(0 if active else 1)


def flash_crazy():
	while True:
		set_all(False)

		for light_index, light_pin in enumerate(light_pins):
			light_pin.value(1 if config.STATUS_LED_ACTIVE_HIGH else 0)
			time.sleep_ms(35)
			light_pin.value(0 if config.STATUS_LED_ACTIVE_HIGH else 1)

		for burst_number in range(8):
			set_all(burst_number % 2 == 0)
			time.sleep_ms(45)

		set_all(True)
		time.sleep_ms(180)
		set_all(False)
		time.sleep_ms(80)


try:
	print("Flashing", len(light_pins), "light(s). Press Ctrl-C to stop.")
	flash_crazy()
except KeyboardInterrupt:
	set_all(False)
	print("Lights off")
