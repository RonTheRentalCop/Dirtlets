# Camera stream (ESP32-CAM, MicroPython)

The AI Thinker ESP32-CAM streams video over Wi-Fi. The Mac runs the depth model ([Core/depth-nav](../../../Core/depth-nav/README.md)) and sends drive commands to the motor board. This board only streams video.

```
ESP32-CAM ──MJPEG video over Wi-Fi──► Mac (depth model + trained model) ──UDP "DRIVE d s"──► motor ESP32
```

## 1. Flash MicroPython with the camera driver (once)

Regular MicroPython has no camera driver, so this board needs a MicroPython build that includes one: [micropython-camera-API](https://github.com/cnadler86/micropython-camera-API). Unlike the motor board, this step replaces the board's firmware.

1. Download `mpy_cam-v1.27.0-AI_THINKER.zip` from the [releases page](https://github.com/cnadler86/micropython-camera-API/releases) and unzip it.
2. The ESP32-CAM has no USB port. Plug it into an ESP32-CAM-MB adapter (or a USB-to-serial adapter with **IO0 wired to GND** while flashing).
3. Flash it with the web flasher at <https://esp.huhn.me/>, or with esptool. For the original ESP32, MicroPython goes at offset `0x1000`:

   ```sh
   pip install esptool
   esptool.py --port /dev/cu.usbserial-XXXX erase_flash
   esptool.py --port /dev/cu.usbserial-XXXX --baud 460800 write_flash 0x1000 firmware.bin
   ```

   If the zip contains separate bootloader and partition files instead of one `firmware.bin`, use the web flasher, which handles the offsets.
4. Remove the IO0–GND wire (if you used one) and press reset.

## 2. Upload the stream program

```sh
cd firmware/micropython/camera_stream
cp wifi_secrets.example.py wifi_secrets.py   # then put your Wi-Fi name and password in it
./upload.sh /dev/cu.usbserial-XXXX
```

`wifi_secrets.py` is in `.gitignore`, so the password stays on your computer. Check `ls /dev/cu.*` if the port changes.

Watch the board start up with `mpremote connect /dev/cu.usbserial-XXXX repl`. It prints:

```
Ready. Stream: http://192.168.1.60:81/stream  (or http://dirtlets-cam.local:81/stream)
```

Open that address in a browser to check the picture.

## 3. Drive from the Mac

```sh
cd Core/depth-nav
.venv/bin/python trainer_gui.py --camera http://192.168.1.60:81/stream
```

Choose **Output → UDP (Dirtlet)**, type the **motor board's** IP, start with a low **Robot speed**, then switch to **Drive**. **Esc** or the red button stops the robot.

## Settings (`config.py`)

| Setting | Default | Notes |
|---|---|---|
| `FRAME_SIZE` | `"VGA"` | 640×480. Use `"QVGA"` (320×240) if the video lags. The depth model works fine on small frames. |
| `JPEG_QUALITY` | `80` | 0–100. Lower means smaller frames, so faster over Wi-Fi. |
| `FLIP_VERTICAL` / `MIRROR_HORIZONTAL` | `False` | Fix the picture if the camera is mounted upside down. |
| `HTTP_PORT` | `81` | |
| `SEND_TIMEOUT_S` | `2` | Drops a stalled viewer so the Mac can reconnect. |

## Safety

The car doesn't depend on this board to stop. The Mac resends drive commands 10 times a second and sends `STOP` if no new video frame arrives for 0.3 s. On top of that, the motor board stops by itself after 500 ms without any command.
