# MicroPython motor controller

This is the active firmware path for the ESP32-WROOM-32E. It uploads Python files without erasing the MicroPython firmware.

## Files

- `main.py`: starts Wi-Fi, motors, lights, UDP, and the safety loop
- `config.py`: edit Wi-Fi, pins, timeout, and LED settings
- `motor.py`: TB6612FNG PWM and direction control
- `udp_control.py`: UDP commands and automatic timeout stop
- `lights.py`: status-light control

## Current Wiring

The current pin assignments are stored in `config.py`:

| TB6612FNG signal | ESP32 GPIO |
| --- | ---: |
| PWMA | 25 |
| AIN1 | 26 |
| AIN2 | 27 |
| PWMB | 14 |
| BIN1 | 18 |
| BIN2 | 19 |
| STBY | 3V3 |

The MPU-650 wiring is SDA to GPIO 21 and SCL to GPIO 22. VCC is 3V3 and all grounds are common. The other MPU-650 pins XDA, XCL, ADO, and INT are not connected yet; sensor-reading code is not added yet.

The firmware currently keeps STBY high because it is wired directly to 3V3, so a software stop sets both motor PWM outputs to zero but does not electrically disable the driver.

## Install the files

`mpremote` is installed on this Mac. On another computer, install it with:

```sh
brew install pipx
pipx install mpremote
```

Find the board port after plugging it in:

```sh
ls /dev/cu.*
```

Edit `config.py`, then upload all files. Replace the port with the one for your board:

```sh
mpremote connect /dev/cu.usbserial-XXXX fs cp config.py :config.py
mpremote connect /dev/cu.usbserial-XXXX fs cp lights.py :lights.py
mpremote connect /dev/cu.usbserial-XXXX fs cp motor.py :motor.py
mpremote connect /dev/cu.usbserial-XXXX fs cp udp_control.py :udp_control.py
mpremote connect /dev/cu.usbserial-XXXX fs cp main.py :main.py
mpremote connect /dev/cu.usbserial-XXXX reset
```

MicroPython automatically runs `main.py` after boot. This code does not flash firmware and does not erase the board.

If Wi-Fi still says `CHANGE_ME`, the board creates an open temporary access point named `Dirtlets-Motor` at `192.168.4.1`. Connect the Mac to that network for the first bench test. For normal use, set `WIFI_SSID` and `WIFI_PASSWORD` in `config.py` and upload that file again.

## Commands

Send UDP packets to the board IP on port `3333`:

```text
STOP
DRIVE 250 250
DRIVE -250 -250
DRIVE 250 -250
```

Commands are signed from `-1000` to `1000`. If no valid command arrives for `500 ms`, both motor PWM outputs are set to zero. STBY remains high because it is wired directly to 3V3.

## Adding features

1. Add new values to `config.py`.
2. Put the hardware logic in its own module, such as `lights.py` or `imu.py`.
3. Import that module from `main.py`.
4. Upload only the changed file with `mpremote ... fs cp file.py :file.py`.
5. Reset the board.

Never power motors from ESP32 GPIO pins. Verify GPIO assignments and test with the wheels lifted.

## Light test

Add verified LED GPIO numbers to `TEST_LIGHT_PINS` in `config.py`. Then run the test without replacing `main.py`:

```sh
mpremote connect /dev/cu.usbserial-XXXX run Board_Test.py
```

Stop it with `Ctrl-C`; the script turns the configured lights off when it exits.

## Motor test

Secure the rover with all wheels lifted and verify the GPIO wiring before running this test. It tests each motor forward and reverse separately at 25% command, then runs both forward briefly. The test sets both PWM outputs to zero when finished or interrupted. If `STBY` is tied high, it remains enabled, but zero PWM stops motor drive.

```sh
mpremote connect /dev/cu.usbserial-XXXX run Motor_Test.py
```
