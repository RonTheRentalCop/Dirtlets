import time

from lidar import RPLidar
from motor import MotorController


TEST_POWER = 600
STEER_POWER = 500
RUN_TIME_MS = 500
PAUSE_MS = 700
FULL_POWER = 1000
FULL_POWER_RUN_TIME_MS = 5000
LIDAR_POLL_MS = 50


def run_step(motors, lidar, label, drive, steer, duration_ms):
    print(label)
    motors.set(drive, steer)
    deadline = time.ticks_add(time.ticks_ms(), duration_ms)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        lidar.poll()
        time.sleep_ms(LIDAR_POLL_MS)
    motors.stop()
    print("  lidar points/rev:", lidar.point_count, "nearest mm:", lidar.nearest_distance_mm)
    time.sleep_ms(PAUSE_MS)


motors = MotorController()
lidar = RPLidar()

try:
    print("Vehicle test: motors and lidar running together. Wheels must be lifted.")
    lidar.start_scan()
    run_step(motors, lidar, "Drive motor forward", TEST_POWER, 0, RUN_TIME_MS)
    run_step(motors, lidar, "Drive motor reverse", -TEST_POWER, 0, RUN_TIME_MS)
    run_step(motors, lidar, "Steering motor left", 0, STEER_POWER, RUN_TIME_MS)
    run_step(motors, lidar, "Steering motor right", 0, -STEER_POWER, RUN_TIME_MS)
    print("Drive motor forward at full power for 5 seconds")
    run_step(motors, lidar, "Drive motor full power", FULL_POWER, 0, FULL_POWER_RUN_TIME_MS)
    print("Vehicle test complete")
except KeyboardInterrupt:
    print("Vehicle test interrupted")
finally:
    motors.stop()
    motors.deinit()
    lidar.stop_scan()
    print("Motors and lidar stopped")
