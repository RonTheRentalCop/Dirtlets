"""Send one motor command from the Mac.

Example:
    python3 send_command.py 192.168.1.50 DRIVE 250 250
"""

import argparse
import socket


parser = argparse.ArgumentParser()
parser.add_argument("host")
parser.add_argument("command", nargs="+")
parser.add_argument("--port", type=int, default=3333)
arguments = parser.parse_args()

message = " ".join(arguments.command).encode("ascii")
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
    sender.sendto(message, (arguments.host, arguments.port))
