# Dirtlets MicroPython firmware

This directory contains the MicroPython firmware for the rover boards. The Mac-side vision, lidar, mapping, and navigation code remains in `Core/`.

Start with `micropython/motor_controller/` for the ESP32-WROOM-32E and TB6612FNG. It uses Wi-Fi and UDP, and it locally stops both motors when valid commands stop arriving.

The camera project will be added as a separate MicroPython project after the exact ESP32-CAM module and camera pin map are confirmed.
