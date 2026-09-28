# Edit this file for your board and local Wi-Fi.

WIFI_SSID = "CHANGE_ME"
WIFI_PASSWORD = "CHANGE_ME"
SETUP_AP_SSID = "Dirtlets-Motor"

UDP_PORT = 3333
COMMAND_TIMEOUT_MS = 500

# Confirmed ESP32-WROOM-32E to TB6612FNG wiring.
MOTOR_A_PWM = 25
MOTOR_A_IN1 = 26
MOTOR_A_IN2 = 27
MOTOR_B_PWM = 14
MOTOR_B_IN1 = 18
MOTOR_B_IN2 = 19
MOTOR_STBY_GPIO = None  # STBY is wired directly to 3V3.

PWM_FREQUENCY_HZ = 1000
PWM_DUTY_MAX = 1023
PWM_MAX = 65535

# MPU-650 I2C wiring. XDA, XCL, ADO, and INT are not connected yet.
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
I2C_FREQUENCY_HZ = 400000

# Common onboard LED on ESP32 DevKit boards. Set to None to disable.
STATUS_LED_PIN = 2
STATUS_LED_ACTIVE_HIGH = True

# Add other LED GPIO numbers here when they are wired and verified.
TEST_LIGHT_PINS = [STATUS_LED_PIN]
