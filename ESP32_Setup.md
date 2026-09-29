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

The board has showed up as `/dev/cu.usbserial-1230`. The serial port can change, so I check `ls /dev/cu.*` again if that one is missing. I upload the motor-controller files with:

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

The values go from `-1000` to `1000`. If the board does not receive a valid command for 500 milliseconds, it sets both motor PWM outputs to zero. STBY is wired to 3V3, so the code does not disable that pin when stopping.

## Current Wiring Map

The current ESP32-WROOM-32E and TB6612FNG connections are:

| TB6612FNG signal | ESP32 connection |
| --- | --- |
| PWMA | GPIO 25 |
| AIN1 | GPIO 26 |
| AIN2 | GPIO 27 |
| PWMB | GPIO 14 |
| BIN1 | GPIO 18 |
| BIN2 | GPIO 19 |
| STBY | 3V3 |
| VCC (logic) | 3V3 |
| VM (motor supply) | Battery positive, within the driver and motor ratings |
| GND | ESP32 GND and battery negative tied together |
| AO1/AO2 | Left motor |
| BO1/BO2 | Right motor |

The MPU-650 is powered from 3V3 and uses SDA on GPIO 21 and SCL on GPIO 22. XDA, XCL, ADO, and INT are not connected yet. The pin values are in `firmware/micropython/motor_controller/config.py`; the MPU-650 reading code still needs to be written.

STBY is connected directly to 3V3, so software stops motion by setting PWM to zero rather than switching the driver to standby.

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
- Also make sure your boards all work I wasted time coding test scripts just to realize the first thing in the manual is if the light does not turn on when plugged in = the board is deed

Assuming the driver is a **TB6612FNG** dual motor driver, here’s the full start-to-finish checklist.

### 1. Gather everything
- ESP32 board
- TB6612FNG motor driver
- 2 DC motors
- External motor battery/power supply
- Jumper wires
- Common ground wire

### 2. Power off
- Unplug USB
- Turn off battery
- Don’t wire while powered

### 3. Make common ground first
- ESP32 **GND** → TB6612 **GND**
- Battery **negative (-)** → same TB6612 **GND**
- All grounds must be connected together

### 4. Logic power
- ESP32 **3.3V** → TB6612 **VCC**
- Do **not** power motors from the ESP32

### 5. Motor power
- Battery **positive (+)** → TB6612 **VM**
- Battery **negative (-)** → common **GND**
- VM is the motor voltage, usually 6V–12V depending on motors

### 6. ESP32 to TB6612 control wires
Example safe pin map:

- ESP32 **GPIO 25** → TB6612 **PWMA**
- ESP32 **GPIO 26** → TB6612 **AIN1**
- ESP32 **GPIO 27** → TB6612 **AIN2**
- ESP32 **GPIO 14** → TB6612 **PWMB**
- ESP32 **GPIO 18** → TB6612 **BIN1**
- ESP32 **GPIO 19** → TB6612 **BIN2**
- ESP32 **GPIO 23** → TB6612 **STBY**

Important:
- **STBY must be HIGH** or the motors will not run
- PWMA/PWMB control speed
- AIN1/AIN2 control Motor A direction
- BIN1/BIN2 control Motor B direction

### 7. Connect motors
- Motor A → TB6612 **AO1** and **AO2**
- Motor B → TB6612 **BO1** and **BO2**
- If a motor spins backward, swap that motor’s two wires

### 8. Code setup
- Set all control pins as `OUTPUT`
- Set **STBY HIGH**
- Use PWM on **PWMA** and **PWMB**
- Direction example:
  - Forward: AIN1 HIGH, AIN2 LOW
  - Reverse: AIN1 LOW, AIN2 HIGH
  - Stop: PWM = 0
- Same idea for BIN1/BIN2

### 9. Test order
- Upload code first
- Connect USB/ESP32 power
- Turn on motor battery
- Set STBY HIGH
- Send low PWM speed first
- Check each motor separately
- Then test both together

### 10. If it doesn’t work
- Check common ground
- Check STBY is HIGH
- Check VM has battery voltage
- Check VCC has 3.3V
- Check PWM pin is correct
- Check motor wires in AO1/AO2 or BO1/BO2
- If ESP32 resets, use separate motor power and add a capacitor across VM/GND

### 11. Shutdown order
- Stop motors in code
- Turn off motor battery
- Unplug ESP32 USB/power

That’s the whole chain: **ESP32 → TB6612FNG → motors**, with power and ground included.rems