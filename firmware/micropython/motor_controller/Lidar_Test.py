import time

from lidar import RPLidar


TEST_DURATION_MS = 5000
REPORT_PERIOD_MS = 500


lidar = RPLidar()

try:
    print("Lidar test starting.")
    lidar.start_scan()
    deadline = time.ticks_add(time.ticks_ms(), TEST_DURATION_MS)
    next_report = time.ticks_add(time.ticks_ms(), REPORT_PERIOD_MS)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        lidar.poll()
        if time.ticks_diff(next_report, time.ticks_ms()) <= 0:
            print("points/rev:", lidar.point_count, "nearest mm:", lidar.nearest_distance_mm)
            next_report = time.ticks_add(time.ticks_ms(), REPORT_PERIOD_MS)
        time.sleep_ms(20)
    print("Lidar test complete")
except KeyboardInterrupt:
    print("Lidar test interrupted")
finally:
    lidar.stop_scan()
    print("Lidar stopped")
