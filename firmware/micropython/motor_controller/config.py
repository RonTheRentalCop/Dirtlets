# Edit this file for your board and local Wi-Fi.

WIFI_SSID = "Lula land"
WIFI_PASSWORD = "4kids2dogs2parents"
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

# RPLIDAR C1 wiring. Motor spins automatically once powered; no motor-control GPIO needed.
LIDAR_UART_ID = 2
LIDAR_TX_PIN = 32  # ESP32 TX -> RPLIDAR RX (green)
LIDAR_RX_PIN = 33  # ESP32 RX -> RPLIDAR TX (yellow)
LIDAR_BAUD_RATE = 460800
LIDAR_SECTOR_COUNT = 16  # 360 / 16 = 22.5 degrees per sector; sector 0 is assumed to face forward.

# Port the host listens on for lidar sector telemetry sent from the board.
TELEMETRY_PORT = 3334
