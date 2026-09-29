# driver_server.py — Mac-side bridge: browser <-> UDP -> ESP32
import socket
from flask import Flask, request, jsonify, Response

ESP32_IP = "10.0.0.3"
ESP32_PORT = 3333
HTTP_PORT = 5050              # 5000 conflicts with macOS AirPlay

app = Flask(__name__)
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_udp(msg):
    udp.sendto(msg.encode("ascii"), (ESP32_IP, ESP32_PORT))

@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")

@app.route("/command", methods=["POST"])
def command():
    data = request.get_json(force=True)
    x = float(data.get("x", 0))   # -1 .. +1 steer
    y = float(data.get("y", 0))   # -1 .. +1 drive
    left = y + x
    right = y - x
    scale = max(abs(left), abs(right), 1.0)
    left = int(left / scale * 1000)
    right = int(right / scale * 1000)
    send_udp("DRIVE %d %d" % (left, right))
    return jsonify(ok=True, left=left, right=right)

@app.route("/stop", methods=["POST"])
def stop():
    send_udp("STOP")
    return jsonify(ok=True)

HTML = r"""<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>Rover Drive</title>
<style>
html,body{margin:0;height:100%;background:#111;color:#eee;
 font-family:system-ui,sans-serif;touch-action:none;overflow:hidden;
 -webkit-user-select:none;user-select:none}
#joy{position:fixed;left:50%;top:45%;width:280px;height:280px;
 margin:-140px 0 0 -140px;border-radius:50%;background:#1e1e1e;border:2px solid #333}
#knob{position:absolute;left:50%;top:50%;width:110px;height:110px;
 margin:-55px 0 0 -55px;border-radius:50%;background:#4af;box-shadow:0 0 20px #4af8}
#status{position:fixed;top:12px;left:12px;font-size:13px;color:#888}
#stop{position:fixed;left:20px;right:20px;bottom:24px;padding:20px;
 font-size:22px;font-weight:700;color:#fff;background:#c33;border:0;border-radius:14px}
#stop:active{background:#e44}
</style></head><body>
<div id="status">ready</div>
<div id="joy"><div id="knob"></div></div>
<button id="stop">STOP</button>
<script>
const joy=document.getElementById('joy'),knob=document.getElementById('knob'),
      statusEl=document.getElementById('status');
let active=false,lastSend=0;
const cmd={x:0,y:0};
function send(force){
  const now=performance.now();
  if(!force && now-lastSend<80) return;
  lastSend=now;
  fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(cmd)})
   .then(()=>{statusEl.textContent=`x ${cmd.x.toFixed(2)}  y ${cmd.y.toFixed(2)}`;})
   .catch(e=>{statusEl.textContent='err: '+e;});
}
function move(ev){
  const r=joy.getBoundingClientRect();
  const cx=r.left+r.width/2, cy=r.top+r.height/2;
  let dx=ev.clientX-cx, dy=ev.clientY-cy;
  const max=r.width/2-30, d=Math.hypot(dx,dy);
  if(d>max){dx=dx/d*max; dy=dy/d*max;}
  knob.style.transform=`translate(${dx}px,${dy}px)`;
  cmd.x=dx/max; cmd.y=-dy/max;
  send(false);
}
function release(){
  active=false; knob.style.transform='translate(0,0)';
  cmd.x=0; cmd.y=0; send(true);
}
joy.addEventListener('pointerdown',e=>{active=true;joy.setPointerCapture(e.pointerId);move(e);});
joy.addEventListener('pointermove',e=>{if(active)move(e);});
joy.addEventListener('pointerup',release);
joy.addEventListener('pointercancel',release);
document.getElementById('stop').addEventListener('click',()=>{release();fetch('/stop',{method:'POST'});});
</script></body></html>"""

if __name__ == "__main__":
    print("Open http://<your-mac-ip>:%d from your phone" % HTTP_PORT)
    app.run(host="0.0.0.0", port=HTTP_PORT, debug=False, threaded=True)