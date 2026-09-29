# Citation: AI-assisted code generation - Claude (Anthropic, 2026).
# AI help was limited to small scripting mistakes and troubleshooting
# while fixing shorted electronics. The code and design are my own.

import argparse
import socket
import time

BOARD_PORT = 3333
TELEMETRY_PORT = 3334

SECTOR_COUNT = 16
SECTOR_WIDTH_DEG = 360.0 / SECTOR_COUNT

MAX_DRIVE_POWER = 300
MAX_STEER_POWER = 300
COMMAND_PERIOD_S = 0.2


def parse_sectors(message):
    if not message.startswith("SECTORS "):
        return None
    values = message[len("SECTORS "):].split(",")
    sectors = []
    for value in values:
        distance = int(value)
        sectors.append(None if distance < 0 else distance)
    return sectors


def choose_target_sector(sectors):
    best_index = None
    best_distance = -1
    for index, distance in enumerate(sectors):
        if distance is not None and distance > best_distance:
            best_distance = distance
            best_index = index
    return best_index


def sector_to_command(target_sector):
    if target_sector is None:
        return 0, 0

    offset = target_sector
    if offset > SECTOR_COUNT / 2:
        offset -= SECTOR_COUNT
    angle_offset_deg = offset * SECTOR_WIDTH_DEG

    drive = MAX_DRIVE_POWER
    steer = int(max(-MAX_STEER_POWER, min(MAX_STEER_POWER, angle_offset_deg / 180.0 * MAX_STEER_POWER)))
    return drive, steer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--board-ip",
        default="192.168.4.1",
        help="ESP32 IP address (default: the Dirtlets-Motor AP address)",
    )
    arguments = parser.parse_args()
    board_ip = arguments.board_ip

    command_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    telemetry_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    telemetry_socket.bind(("0.0.0.0", TELEMETRY_PORT))
    telemetry_socket.settimeout(0.1)

    def send_command(drive, steer):
        message = f"DRIVE {drive} {steer}".encode("ascii")
        command_socket.sendto(message, (board_ip, BOARD_PORT))

    print("Registering with the board at", board_ip)
    send_command(0, 0)

    last_sectors = [None] * SECTOR_COUNT
    next_command_time = time.monotonic()

    try:
        while True:
            try:
                packet, _address = telemetry_socket.recvfrom(256)
                sectors = parse_sectors(packet.decode("ascii"))
                if sectors is not None:
                    last_sectors = sectors
            except socket.timeout:
                pass

            now = time.monotonic()
            if now >= next_command_time:
                target_sector = choose_target_sector(last_sectors)
                drive, steer = sector_to_command(target_sector)
                send_command(drive, steer)
                print("target sector:", target_sector, "drive:", drive, "steer:", steer)
                next_command_time = now + COMMAND_PERIOD_S
    except KeyboardInterrupt:
        print("Stopping")
    finally:
        send_command(0, 0)
        command_socket.close()
        telemetry_socket.close()


if __name__ == "__main__":
    main()
