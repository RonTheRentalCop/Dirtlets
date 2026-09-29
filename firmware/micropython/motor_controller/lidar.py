import time

from machine import UART

import config


SCAN_COMMAND = bytes([0xA5, 0x20])
STOP_COMMAND = bytes([0xA5, 0x25])
RESPONSE_DESCRIPTOR_LENGTH = 7


class RPLidar:
    def __init__(self):
        self._uart = UART(
            config.LIDAR_UART_ID,
            baudrate=config.LIDAR_BAUD_RATE,
            tx=config.LIDAR_TX_PIN,
            rx=config.LIDAR_RX_PIN,
        )
        self._scanning = False
        self.point_count = 0
        self.nearest_distance_mm = None
        self._revolution_points = 0
        self._revolution_nearest = None

        self.sector_count = config.LIDAR_SECTOR_COUNT
        self.sector_width_deg = 360.0 / self.sector_count
        self._sector_min = [None] * self.sector_count
        self.last_sectors = [None] * self.sector_count
        self.new_revolution = False

    def start_scan(self):
        self._uart.write(SCAN_COMMAND)
        descriptor = self._read_exact(RESPONSE_DESCRIPTOR_LENGTH)
        if descriptor is None or descriptor[0] != 0xA5 or descriptor[1] != 0x5A:
            raise RuntimeError("no valid RPLIDAR scan response; check UART wiring and power")
        self._scanning = True
        self._revolution_points = 0
        self._revolution_nearest = None

    def stop_scan(self):
        self._uart.write(STOP_COMMAND)
        self._scanning = False
        time.sleep_ms(50)

    def _read_exact(self, length):
        buffer = b""
        deadline = time.ticks_add(time.ticks_ms(), 1000)
        while len(buffer) < length:
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return None
            chunk = self._uart.read(length - len(buffer))
            if chunk:
                buffer += chunk
        return buffer

    def poll(self):
        """Read whatever scan packets are available. Call this often from the main loop."""
        if not self._scanning:
            return
        available = self._uart.any()
        if not available:
            return
        chunk = self._uart.read(available - (available % 5))
        if not chunk:
            return
        for offset in range(0, len(chunk), 5):
            self._handle_packet(chunk[offset:offset + 5])

    def _handle_packet(self, packet):
        byte0, byte1, byte2, byte3, byte4 = packet
        start_flag = byte0 & 0x01
        inverse_start_flag = (byte0 >> 1) & 0x01
        check_bit = byte1 & 0x01
        if start_flag == inverse_start_flag or check_bit != 1:
            return  # misaligned packet; drop and resync on the next poll

        if start_flag and self._revolution_points > 0:
            self.point_count = self._revolution_points
            self.nearest_distance_mm = self._revolution_nearest
            self.last_sectors = self._sector_min
            self.new_revolution = True
            self._revolution_points = 0
            self._revolution_nearest = None
            self._sector_min = [None] * self.sector_count

        distance_mm = (byte3 | (byte4 << 8)) / 4.0
        if distance_mm > 0:
            if self._revolution_nearest is None or distance_mm < self._revolution_nearest:
                self._revolution_nearest = distance_mm
            self._revolution_points += 1

            angle_low = (byte1 >> 1) & 0x7F
            angle_deg = ((byte2 << 7) | angle_low) / 64.0
            sector = int(angle_deg / self.sector_width_deg) % self.sector_count
            current = self._sector_min[sector]
            if current is None or distance_mm < current:
                self._sector_min[sector] = distance_mm
