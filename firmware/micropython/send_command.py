# Citation: AI-assisted code generation - Claude (Anthropic, 2026).
# AI help was limited to small scripting mistakes and troubleshooting
# while fixing shorted electronics. The code and design are my own.

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
