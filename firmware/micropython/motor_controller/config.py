# Citation: AI-assisted code generation - Claude (Anthropic, 2026).
# AI help was limited to small scripting mistakes and troubleshooting
# while fixing shorted electronics. The code and design are my own.

WIFI_SSID = "CHANGE_ME"
WIFI_PASSWORD = "CHANGE_ME"
SETUP_AP_SSID = "Dirtlets-Motor"

UDP_PORT = 3333
COMMAND_TIMEOUT_MS = 500

MOTOR_A_PWM = 25
MOTOR_A_IN1 = 26
MOTOR_A_IN2 = 27
MOTOR_B_PWM = 14
MOTOR_B_IN1 = 18
MOTOR_B_IN2 = 19
MOTOR_STBY_GPIO = None

PWM_FREQUENCY_HZ = 1000
PWM_DUTY_MAX = 1023
PWM_MAX = 65535

I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
I2C_FREQUENCY_HZ = 400000

STATUS_LED_PIN = 2
STATUS_LED_ACTIVE_HIGH = True

TEST_LIGHT_PINS = [STATUS_LED_PIN]
