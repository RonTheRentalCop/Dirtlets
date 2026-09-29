import socket

import config


class Telemetry:
    def __init__(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host_address = None

    def set_host(self, ip_address):
        self.host_address = (ip_address, config.TELEMETRY_PORT)

    def send_sectors(self, sectors):
        if self.host_address is None:
            return
        values = ",".join(str(-1 if value is None else int(value)) for value in sectors)
        message = ("SECTORS " + values).encode("ascii")
        try:
            self._socket.sendto(message, self.host_address)
        except OSError:
            pass
