import socket
import time

import config


class CommandReceiver:
    def __init__(self, motor_controller, status_light):
        self._motor_controller = motor_controller
        self._status_light = status_light
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("0.0.0.0", config.UDP_PORT))
        self._socket.settimeout(0.05)
        self._last_command_ms = time.ticks_ms()

    @staticmethod
    def _parse(message):
        words = message.strip().split()
        if not words:
            return None
        if words[0] == "STOP" and len(words) == 1:
            return 0, 0
        if words[0] == "DRIVE" and len(words) == 3:
            try:
                left = int(words[1])
                right = int(words[2])
            except ValueError:
                return None
            if -1000 <= left <= 1000 and -1000 <= right <= 1000:
                return left, right
        return None

    def poll(self):
        try:
            packet, address = self._socket.recvfrom(96)
        except OSError:
            return

        try:
            message = packet.decode("ascii")
        except UnicodeError:
            return

        command = self._parse(message)
        if command is None:
            return

        self._motor_controller.set(command[0], command[1])
        self._last_command_ms = time.ticks_ms()
        self._status_light.on()

    def enforce_timeout(self):
        elapsed = time.ticks_diff(time.ticks_ms(), self._last_command_ms)
        if elapsed > config.COMMAND_TIMEOUT_MS:
            self._motor_controller.stop()
            self._status_light.off()

    def close(self):
        self._motor_controller.stop()
        self._socket.close()
