#!/bin/zsh
set -e

if [[ $# -ne 1 ]]; then
    print "Usage: ./upload.sh /dev/cu.usbserial-XXXX"
    exit 2
fi

if [[ ! -f wifi_secrets.py ]]; then
    print "Missing wifi_secrets.py: copy wifi_secrets.example.py to wifi_secrets.py and add your Wi-Fi first."
    exit 2
fi

board_port="$1"
files=(config.py wifi_secrets.py wifi.py main.py)
for file in $files; do
    mpremote connect "$board_port" fs cp "$file" ":$file"
done
mpremote connect "$board_port" reset
print "Uploaded MicroPython camera stream to $board_port"
