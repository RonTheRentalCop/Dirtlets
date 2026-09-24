# Citation: AI-assisted code generation - Claude (Anthropic, 2026).
# AI help was limited to small scripting mistakes and troubleshooting
# while fixing shorted electronics. The code and design are my own.

WIFI_SSID = "CHANGE_ME"
WIFI_PASSWORD = "CHANGE_ME"
SETUP_AP_SSID = "Dirtlets-Motor"

UDP_PORT = 3333
COMMAND_TIMEOUT_MS = 500
MOTOR_A_PWM = 25
MOTOR_A_IN1 = 27
MOTOR_A_IN2 = 14
MOTOR_B_PWM = 26
MOTOR_B_IN1 = 32
MOTOR_B_IN2 = 4
MOTOR_STBY = 33

PWM_FREQUENCY_HZ = 20000
PWM_MAX = 65535

STATUS_LED_PIN = 2
STATUS_LED_ACTIVE_HIGH = True

TEST_LIGHT_PINS = [STATUS_LED_PIN]
