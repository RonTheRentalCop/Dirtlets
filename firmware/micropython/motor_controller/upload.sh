#!/bin/zsh
set -e

if [[ $# -ne 1 ]]; then
    print "Usage: ./upload.sh /dev/cu.usbserial-XXXX"
    exit 2
fi

board_port="$1"
files=(config.py lights.py motor.py udp_control.py main.py)
for file in $files; do
    mpremote connect "$board_port" fs cp "$file" ":$file"
done
mpremote connect "$board_port" reset
print "Uploaded MicroPython motor controller to $board_port"
