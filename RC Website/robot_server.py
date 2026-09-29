# robot_server.py
from flask import Flask, request, jsonify, Response
import threading, time

app = Flask(__name__)

# ---------- MOTOR CONTROL ----------
class MotorController:
    def __init__(self):
        self.left = 0.0
        self.right = 0.0
        self.last_cmd = time.time()
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def set(self, left, right):
        with self.lock:
            self.left = max(-1.0, min(1.0, float(left)))
            self.right = max(-1.0, min(1.0, float(right)))
            self.last_cmd = time.time()

    def stop(self):
        self.set(0, 0)

    def _loop(self):
        while self.running:
            with self.lock:
                left, right = self.left, self.right
                age = time.time() - self.last_cmd
            if age > 0.5:          # watchdog: stop if no command for 0.5s
                left = right = 0.0
            self.apply_motors(left, right)
            time.sleep(0.02)       # 50 Hz

    def apply_motors(self, left, right):
        # ---- REPLACE THIS WITH YOUR HARDWARE ----
        # left/right are -1.0 to +1.0
        # For testing, just print:
        print(f"L={left:+.2f} R={right:+.2f}", end="\r")

        # Example Raspberry Pi GPIO with gpiozero:
        # from gpiozero import Motor
        # left_motor = Motor(forward=17, backward=18)
        # right_motor = Motor(forward=22, backward=23)
        # left_motor.value = left
        # right_motor.value = right

        # Example serial to Arduino:
        # ser.write(f"L{int(left*255)} R{int(right*255)}\n".encode())

motor = MotorController()

@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")

@app.route("/command", methods=["POST"])
def command():
    data = request.get_json(force=True)
    x = float(data.get("x", 0))   # -1 left .. +1 right
    y = float(data.get("y", 0))   # -1 back .. +1 forward
    # Tank-drive mixing
    left = y + x
    right = y - x
    m = max(abs(left), abs(right), 1.0)
    left /= m
    right /= m
    motor.set(left, right)
    return jsonify(ok=True, left=left, right=right)

@app.route("/stop", methods=["POST"])
def stop():
    motor.stop()
    return jsonify(ok=True)

HTML = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Robot Drive</title>
<style>
  body { margin:0; font-family:system-ui, sans-serif; background:#111; color:#eee; touch-action:none; }
  #pad { position:fixed; inset:0; }
  .joystick { position:absolute; left:50%; top:50%; width:260px; height:260px; margin:-130px 0 0 -130px; border-radius:50%; background:#222; border:2px solid #444; }
  .knob { position:absolute; left:50%; top:50%; width:100px; height:100px; margin:-50px 0 0 -50px; border-radius:50%; background:#4af; box-shadow:0 0 20px #4af8; }
  .buttons { position:fixed; bottom:20px; left:20px; right:20px; display:flex; gap:12px; justify-content:center; }
  button { flex:1; max-width:160px; padding:18px; font-size:18px; border:0; border-radius:12px; background:#333; color:#fff; }
  button.stop { background:#c33; }
  #status { position:fixed; top:10px; left:10px; font-size:12px; color:#888; }
</style>
</head>
<body>
<div id="status">connecting…</div>
<div id="pad">
  <div class="joystick" id="joy"><div class="knob" id="knob"></div></div>
</div>
<div class="buttons">
  <button id="forward">Forward</button>
  <button id="back">Back</button>
  <button id="left">Left</button>
  <button id="right">Right</button>
  <button class="stop" id="stop">STOP</button>
</div>
<script>
const joy = document.getElementById('joy');
const knob = document.getElementById('knob');
const status = document.getElementById('status');
let active = false;
let lastSent = 0;
let cmd = {x:0, y:0};

function send() {
  const now = Date.now();
  if (now - lastSent < 80) return;
  lastSent = now;
  fetch('/command', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(cmd)
  }).then(r => r.json()).then(d => {
    status.textContent = `L ${d.left.toFixed(2)}  R ${d.right.toFixed(2)}`;
  }).catch(e => status.textContent = 'error: ' + e);
}

function setFromEvent(e) {
  const rect = joy.getBoundingClientRect();
  const cx = rect.left + rect.width/2;
  const cy = rect.top + rect.height/2;
  let dx = e.clientX - cx;
  let dy = e.clientY - cy;
  const max = rect.width/2 - 20;
  const dist = Math.hypot(dx, dy);
  if (dist > max) { dx = dx/dist*max; dy = dy/dist*max; }
  const x = dx / max;
  const y = -dy / max;
  cmd.x = x; cmd.y = y;
  knob.style.transform = `translate(${dx}px, ${dy}px)`;
  send();
}

function reset() {
  active = false;
  cmd.x = 0; cmd.y = 0;
  knob.style.transform = 'translate(0,0)';
  send();
}

joy.addEventListener('pointerdown', e => { active = true; joy.setPointerCapture(e.pointerId); setFromEvent(e); });
joy.addEventListener('pointermove', e => { if (active) setFromEvent(e); });
joy.addEventListener('pointerup', reset);
joy.addEventListener('pointercancel', reset);

document.getElementById('stop').onclick = () => {
  fetch('/stop', {method:'POST'});
  reset();
};

function hold(id, x, y) {
  const el = document.getElementById(id);
  let interval;
  const start = e => { e.preventDefault(); cmd.x=x; cmd.y=y; send(); interval=setInterval(send, 100); };
  const end = e => { e.preventDefault(); clearInterval(interval); reset(); };
  el.addEventListener('pointerdown', start);
  el.addEventListener('pointerup', end);
  el.addEventListener('pointercancel', end);
  el.addEventListener('pointerleave', end);
}
hold('forward', 0, 1);
hold('back', 0, -1);
hold('left', -1, 0);
hold('right', 1, 0);
</script>
</body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)