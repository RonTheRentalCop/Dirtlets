# Edit this file for your board and local Wi-Fi.

WIFI_SSID = "CHANGE_ME"
WIFI_PASSWORD = "CHANGE_ME"
SETUP_AP_SSID = "Dirtlets-Motor"

UDP_PORT = 3333
COMMAND_TIMEOUT_MS = 500

# TB6612FNG pins for the ESP32-WROOM-32E. Verify before powering motors.
MOTOR_A_PWM = 25
MOTOR_A_IN1 = 27
MOTOR_A_IN2 = 14
MOTOR_B_PWM = 26
MOTOR_B_IN1 = 32
MOTOR_B_IN2 = 4
MOTOR_STBY = 33

PWM_FREQUENCY_HZ = 20000
PWM_MAX = 65535

# Common onboard LED on ESP32 DevKit boards. Set to None to disable.
STATUS_LED_PIN = 2
STATUS_LED_ACTIVE_HIGH = True

# Add other LED GPIO numbers here when they are wired and verified.
TEST_LIGHT_PINS = [STATUS_LED_PIN]
