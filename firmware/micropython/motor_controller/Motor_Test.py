import time

from motor import MotorController


TEST_POWER = 600
STEER_POWER = 500
RUN_TIME_MS = 500
PAUSE_MS = 700
FULL_POWER = 1000
FULL_POWER_RUN_TIME_MS = 5000


def run_step(motors, label, drive, steer):
    print(label)
    motors.set(drive, steer)
    time.sleep_ms(RUN_TIME_MS)
    motors.stop()
    time.sleep_ms(PAUSE_MS)


motors = MotorController()

try:
    print("Motor test starting at about 60% PWM. Wheels must be lifted.")
    run_step(motors, "Drive motor forward", TEST_POWER, 0)
    run_step(motors, "Drive motor reverse", -TEST_POWER, 0)
    run_step(motors, "Steering motor left", 0, STEER_POWER)
    run_step(motors, "Steering motor right", 0, -STEER_POWER)
    print("Drive motor forward at full power for 5 seconds")
    motors.set(FULL_POWER, 0)
    time.sleep_ms(FULL_POWER_RUN_TIME_MS)
    motors.stop()
    print("Motor test complete")
except KeyboardInterrupt:
    print("Motor test interrupted")
finally:
    motors.stop()
    motors.deinit()
    print("Motor PWM outputs set to zero")