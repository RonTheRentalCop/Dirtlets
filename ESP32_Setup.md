# ESP 32 Setup

## How will my ESP 32 Boards Work?

<p align="center">
	<a href="https://tenor.com/view/fanum-justfanum-fanum-tax-exploding-broccoli-gif-7470261283146790012">
		<img src="https://media1.tenor.com/m/Z6uzDtFRdHwAAAAC/fanum-justfanum.gif" alt="Fanum tax exploding broccoli GIF" width="420">
	</a>
</p>

## Vocab and Acronyms
#### CC: Central Computer
#### ESP32: A Development board series we decided to use for this project
#### ESP32-CAM: A Developement board series we used for RGB Vision. 

### We will use our first ESP32 for drive and safety. 

With this Dev Board we will want to 
- Capture Video
- Stream Video Over WIFI or ESP NOW
- Read Simple Sensors
- Send Battery and Status Data
- Recieve some commands from the centeral computer

### We will use our ESP32-CAM to conduct vision and telemetry.
- Control the Motor Driver Booard
- Read Wheel Encoders (You have to have these for accurate data)
- Read the MPU-650 IMU
- Recive Movement commands from the CC

### FYI: Don't power the motors directly from the pins just use the ESP to send signals to the motor driveer while the battery powers the moters THROUGH THE DRIVER

<img src="Photos/Screenshot 2026-09-22 at 9.14.26 AM.png" width="600">

## Using the Boards
1. The boards already use MicroPython, so I am not using the Arduino IDE or ESP-IDF for the active firmware.
2. The Mac uses `mpremote` to send Python files to the board over USB without erasing MicroPython.
3. The motor-controller files are in `firmware/micropython/motor_controller/`.
4. `config.py` is where I change the Wi-Fi settings, GPIO pins, light pins, UDP port, and motor timeout.
5. `main.py` starts the Wi-Fi, motors, lights, UDP receiver, and safety timeout.
6. I test the lights separately before testing the motor driver.
7. The motor driver should be tested with the wheels lifted off the table.

The Mac setup uses a project `requirements.txt` with `mpremote`. From the project folder I can install it with:

```sh
./.venv/bin/python -m pip install -r requirements.txt
```

After plugging in the board, I find its serial port with:

```sh
ls /dev/cu.*
```

The current board showed up as `/dev/cu.usbserial-1220`. I upload the motor-controller files with:

```sh
cd firmware/micropython/motor_controller
./upload.sh /dev/cu.usbserial-1220
```

This uploads the Python files and resets the MicroPython program. It does not erase the board or install a different firmware.

For example some motor commands could be
-
- STOP
- FORWARD 100
- REVERSE 100
- LEFT 80
- RIGHT 80

Then we will want to test over the network. The first working connection uses UDP instead of a web server.

Do not use these requests for the whole project witch to UDP MQTT or websockets for a more structured prototcol

The current UDP commands are:

```text
STOP
DRIVE 250 250
DRIVE -250 -250
DRIVE 250 -250
```

The values go from `-1000` to `1000`. If the board does not receive a valid command for 500 milliseconds, it stops both motors and disables the TB6612FNG standby pin. This is important because losing Wi-Fi should not leave the rover driving.

## Testing the Lights

The light test is separate from the main motor program. The configured light pins are in `config.py`:

```python
TEST_LIGHT_PINS = [2]
```

I can add more verified LED GPIO pins to that list. From the motor-controller folder I run:

```sh
mpremote connect /dev/cu.usbserial-1220 run Board_Test.py
```

This flashes the configured lights quickly and turns them off when I press `Ctrl-C`. It does not replace `main.py`.

## Start the ESP 32 Cam Seperately 
1. First we need to just confirm if it works
2. Run a basic camera web server
3. connect to the wifi hosted from pc
4. Open the stream
5. Run some compatibility tests with open cv

## Things to watch out for 
- ESP32 GPIO pins use 3.3 V logic.
- Do not feed 5 V directly into a GPIO pin.
- Motors create electrical noise and voltage spikes.
- Use a separate regulated supply for the ESP32.
- Connect all grounds together between the ESP32, driver, and sensor systems.
- Add a physical power switch or emergency disconnect.
- Test LiPo wiring carefully and never leave exposed conductors near each other.
- The ESP32-CAM may require an external USB-to-serial programmer for uploading code.
- Some ESP32-CAM pins are already used by the camera or flash, so pin selection matters.
- Also make sure your boards all work I wasted time coding test scripts just to realize the first thing in the manual is if the light does not turn on when plugged in = the board is dead