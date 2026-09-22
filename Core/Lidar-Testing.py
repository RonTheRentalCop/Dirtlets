import asyncio
import math
import queue
import sys
import threading

import cv2
import numpy as np

from rplidarc1 import RPLidar


BAUD_RATE = 460800
WINDOW_NAME = "RPLIDAR C1 Test"
CANVAS_SIZE = 720
MAX_DISTANCE_MM = 8000
MARGIN = 55


def find_port():
    from serial.tools import list_ports

    ports = list(list_ports.comports())
    for port in ports:
        description = f"{port.device} {port.description or ''}".lower()
        if any(name in description for name in ("usb", "serial", "lidar", "cp210", "ch340")):
            return port.device
    return None


class LidarReader:
    def __init__(self, port):
        self.port = port
        self.points = queue.Queue()
        self.stop_requested = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_requested.set()

    def _run(self):
        lidar = None
        try:
            lidar = RPLidar(self.port, BAUD_RATE)
            self.points.put(("status", f"Connected to {self.port}. Scanning..."))
            asyncio.run(self._scan(lidar))
        except Exception as error:
            self.points.put(("error", f"Lidar error: {error}"))
        finally:
            if lidar is not None:
                try:
                    lidar.reset()
                except Exception:
                    pass
                try:
                    lidar.shutdown()
                except Exception:
                    pass
            self.points.put(("stopped", "Scan stopped."))

    async def _scan(self, lidar):
        scan_task = asyncio.create_task(lidar.simple_scan())
        try:
            while not self.stop_requested.is_set():
                try:
                    point = await asyncio.wait_for(lidar.output_queue.get(), timeout=0.25)
                except asyncio.TimeoutError:
                    continue
                if isinstance(point, dict):
                    self.points.put(("point", point))
        finally:
            lidar.stop_event.set()
            await asyncio.gather(scan_task, return_exceptions=True)


def draw_scan(scan_points, status, error_message=None):
    image = np.full((CANVAS_SIZE, CANVAS_SIZE, 3), 255, dtype=np.uint8)
    center = CANVAS_SIZE // 2
    radius = center - MARGIN

    for fraction in (0.25, 0.5, 0.75, 1.0):
        ring_radius = int(radius * fraction)
        cv2.circle(image, (center, center), ring_radius, (215, 225, 228), 1)

    cv2.line(image, (MARGIN, center), (CANVAS_SIZE - MARGIN, center), (225, 230, 232), 1)
    cv2.line(image, (center, MARGIN), (center, CANVAS_SIZE - MARGIN), (225, 230, 232), 1)

    for angle, distance in scan_points.items():
        scaled_distance = min(distance / MAX_DISTANCE_MM, 1.0) * radius
        radians = math.radians(angle - 90)
        x = int(center + scaled_distance * math.cos(radians))
        y = int(center + scaled_distance * math.sin(radians))
        cv2.circle(image, (x, y), 2, (23, 107, 120), -1)

    cv2.putText(image, "0 deg", (center - 25, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (82, 99, 107), 1)
    cv2.putText(image, "90 deg", (CANVAS_SIZE - 95, center - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (82, 99, 107), 1)
    cv2.putText(image, "180 deg", (center - 35, CANVAS_SIZE - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (82, 99, 107), 1)
    cv2.putText(image, "270 deg", (10, center - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (82, 99, 107), 1)

    nearest = min(scan_points.values()) if scan_points else None
    cv2.putText(image, f"{status} | points: {len(scan_points)}", (15, CANVAS_SIZE - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (31, 45, 51), 1)
    cv2.putText(image, f"nearest: {nearest:.0f} mm" if nearest else "nearest: --", (15, CANVAS_SIZE - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (31, 45, 51), 1)
    if error_message:
        cv2.putText(image, "Press q to quit", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 180), 1)

    return image

def parse_float(value, default=None):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else find_port()
    if not port:
        print("No serial port found. Run with the port, for example:")
        print(".venv/bin/python Core/Lidar-Testing.py /dev/cu.usbserial-XXXX")
        return 1

    reader = LidarReader(port)
    reader.start()
    scan_points = {}
    status = f"Connecting to {port}..."
    error_message = None

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    while True:
        while True:
            try:
                kind, value = reader.points.get_nowait()
            except queue.Empty:
                break

            if kind == "point":
                if not isinstance(value, dict):
                    continue

                distance = parse_float(value.get("d_mm"))
                angle = parse_float(value.get("a_deg"))

                if distance is None or angle is None:
                    continue

                if distance > 0:
                    scan_points[angle] = distance

            elif kind == "error":
                error_message = value
                status = value
            else:
                status = value

        cv2.imshow(WINDOW_NAME, draw_scan(scan_points, status, error_message))
        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            break

    reader.stop()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())