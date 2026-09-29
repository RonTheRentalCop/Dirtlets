"""Web-based dual-joystick remote control for the rover.

Left joystick (vertical axis): drive motor forward/reverse.
Right joystick (horizontal axis): steering motor left/right.

Run this on the Mac, then open http://localhost:8000/ (or the Mac's LAN IP
from another device on the same network) in a browser.
"""

import argparse
import json
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BOARD_PORT = 3333
MAX_DRIVE_POWER = 300
MAX_STEER_POWER = 300
COMMAND_TIMEOUT_S = 0.5

PAGE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dirtlets Remote Control</title>
<style>
  body { background: #111; color: #eee; font-family: sans-serif; text-align: center; }
  .row { display: flex; justify-content: center; gap: 40px; margin-top: 30px; }
  .joystick-base {
    width: 160px; height: 160px; border-radius: 50%;
    background: #222; border: 2px solid #444; position: relative; touch-action: none;
  }
  .joystick-knob {
    width: 60px; height: 60px; border-radius: 50%;
    background: #4caf50; position: absolute; left: 50px; top: 50px;
  }
  .label { margin-top: 10px; font-size: 14px; color: #aaa; }
  #stop {
    margin-top: 30px; padding: 16px 40px; font-size: 20px;
    background: #b71c1c; color: white; border: none; border-radius: 8px;
  }
  #status { margin-top: 15px; color: #888; font-size: 13px; }
</style>
</head>
<body>
<h2>Dirtlets Remote Control</h2>
<div class="row">
  <div>
    <div class="joystick-base" id="driveBase"><div class="joystick-knob" id="driveKnob"></div></div>
    <div class="label">DRIVE (forward / reverse)</div>
  </div>
  <div>
    <div class="joystick-base" id="steerBase"><div class="joystick-knob" id="steerKnob"></div></div>
    <div class="label">STEER (left / right)</div>
  </div>
</div>
<button id="stop">STOP</button>
<div id="status">drive: 0, steer: 0</div>

<script>
const MAX_DRIVE_POWER = 300;
const MAX_STEER_POWER = 300;
const SEND_PERIOD_MS = 150;

let driveValue = 0;
let steerValue = 0;

function setupJoystick(baseId, knobId, onChange) {
  const base = document.getElementById(baseId);
  const knob = document.getElementById(knobId);
  const radius = base.clientWidth / 2 - knob.clientWidth / 2;
  let active = false;

  function moveKnob(dx, dy) {
    const distance = Math.min(Math.hypot(dx, dy), radius);
    const angle = Math.atan2(dy, dx);
    const clampedX = Math.cos(angle) * distance;
    const clampedY = Math.sin(angle) * distance;
    knob.style.left = (radius + clampedX) + "px";
    knob.style.top = (radius + clampedY) + "px";
    onChange(clampedX / radius, clampedY / radius);
  }

  function resetKnob() {
    knob.style.left = radius + "px";
    knob.style.top = radius + "px";
    onChange(0, 0);
  }

  base.addEventListener("pointerdown", (event) => {
    active = true;
    base.setPointerCapture(event.pointerId);
  });
  base.addEventListener("pointermove", (event) => {
    if (!active) return;
    const rect = base.getBoundingClientRect();
    moveKnob(event.clientX - rect.left - radius, event.clientY - rect.top - radius);
  });
  base.addEventListener("pointerup", () => { active = false; resetKnob(); });
  base.addEventListener("pointercancel", () => { active = false; resetKnob(); });

  resetKnob();
}

setupJoystick("driveBase", "driveKnob", (normalizedX, normalizedY) => {
  driveValue = Math.round(-normalizedY * MAX_DRIVE_POWER);
});
setupJoystick("steerBase", "steerKnob", (normalizedX, normalizedY) => {
  steerValue = Math.round(normalizedX * MAX_STEER_POWER);
});

function sendCommand(drive, steer) {
  fetch("/command", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ drive: drive, steer: steer }),
  }).catch(() => {});
  document.getElementById("status").textContent = "drive: " + drive + ", steer: " + steer;
}

document.getElementById("stop").addEventListener("click", () => {
  driveValue = 0;
  steerValue = 0;
  sendCommand(0, 0);
});

setInterval(() => sendCommand(driveValue, steerValue), SEND_PERIOD_MS);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    board_ip = "192.168.4.1"
    command_socket = None

    def log_message(self, format_string, *args):
        pass  # keep the console quiet during normal operation

    def do_GET(self):
        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            return
        body = PAGE_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/command":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length))
            drive = int(payload["drive"])
            steer = int(payload["steer"])
        except (ValueError, KeyError, json.JSONDecodeError):
            self.send_response(400)
            self.end_headers()
            return

        drive = max(-MAX_DRIVE_POWER, min(MAX_DRIVE_POWER, drive))
        steer = max(-MAX_STEER_POWER, min(MAX_STEER_POWER, steer))
        message = f"DRIVE {drive} {steer}".encode("ascii")
        Handler.command_socket.sendto(message, (Handler.board_ip, BOARD_PORT))

        self.send_response(204)
        self.end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board-ip", default="192.168.4.1", help="ESP32 IP address")
    parser.add_argument("--port", type=int, default=8000, help="Web server port")
    arguments = parser.parse_args()

    Handler.board_ip = arguments.board_ip
    Handler.command_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server = ThreadingHTTPServer(("0.0.0.0", arguments.port), Handler)
    print(f"Sending drive commands to {arguments.board_ip}:{BOARD_PORT}")
    print(f"Open http://localhost:{arguments.port}/ in a browser")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        Handler.command_socket.sendto(b"STOP", (arguments.board_ip, BOARD_PORT))
        server.server_close()
        print("Stopped")


if __name__ == "__main__":
    main()
