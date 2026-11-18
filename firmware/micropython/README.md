# Dirtlets MicroPython firmware

The MicroPython projects live here because the boards are already running MicroPython. Do not use the ESP-IDF `idf.py flash` workflow for these boards.

Start with `motor_controller/`. The AI Thinker ESP32-CAM runs `camera_stream/`, which streams video to the Mac. See [camera_stream/README.md](camera_stream/README.md). That board needs a MicroPython build with the camera driver flashed once.
