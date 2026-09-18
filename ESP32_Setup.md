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
- Read Wheel Encoders (Only if they are wheels if on treads its irrelevant)
- Read the MPU-650 IMU
- Recive Movement commands from the CC

### FYI: Don't power the motors directly from the pins just use the ESP to send signals to the motor driveer while the battery powers the moters THROUGH THE DRIVER

## Using the Boards
1. To start ysing the ESP32 we need to install the Arduino IDE or PlatformIO
2. Then we need to add the ESP32 board package
3. Upload a Blink Program (basic program to check if the board is alive)
4. Open Serial Monitor and print the sensor values
5. Connect the motor driver with the wheels lifted off the table
6. Test one motor forward, stop, and reverse.
7. You could add communication timeouts that stops the motors if the commands are not arriving for whatever reason

For example some motor commands could be
-
- STOP
- FORWARD 100
- REVERSE 100
- LEFT 80
- RIGHT 80

Then we will want to test over network so the easiest waty will be hosting a simple web sever from your computer and send requests

Do not use these requests for the whole project witch to UDP MQTT or websockets for a more structured prototcol

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