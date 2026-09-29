# driver_server.py — PC-side bridge: browser <-> UDP -> ESP32
import socket
from flask import Flask, request, jsonify, Response

ESP32_IP = "10.0.0.24"
ESP32_PORT = 3333
HTTP_PORT = 5050

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
    x = float(data.get("x", 0))   # -1 .. +1 steer  (Steer stick)
    y = float(data.get("y", 0))   # -1 .. +1 drive  (Drive stick)
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
html,body{margin:0;height:100%;background:#000;color:#fff;
 font-family:system-ui,sans-serif;touch-action:none;overflow:hidden;
 -webkit-user-select:none;user-select:none}
#status{position:fixed;top:12px;left:0;right:0;text-align:center;
 font-size:13px;letter-spacing:.08em;color:#fff;font-variant-numeric:tabular-nums}
#pads{position:fixed;top:40px;bottom:96px;left:0;right:0;display:flex;
 align-items:center;justify-content:space-around;gap:16px;padding:0 16px}
.pad{display:flex;flex-direction:column;align-items:center;gap:10px}
.label{font-size:12px;letter-spacing:.2em;text-transform:uppercase}
.track{position:relative;border:2px solid #fff;border-radius:999px}
#drive{width:90px;height:min(260px,55vh)}
#steer{width:min(260px,40vw);height:90px}
@media (orientation:portrait){
 #pads{flex-direction:column;justify-content:space-evenly}
 #drive{height:min(260px,34vh)}
 #steer{width:min(320px,85vw)}
}
.knob{position:absolute;left:50%;top:50%;width:70px;height:70px;
 margin:-35px 0 0 -35px;border-radius:50%;background:#fff;pointer-events:none}
.track.active .knob{background:#000;border:3px solid #fff;box-sizing:border-box}
#stop{position:fixed;left:16px;right:16px;bottom:20px;padding:18px;
 font-size:22px;font-weight:700;letter-spacing:.2em;color:#000;background:#fff;
 border:0;border-radius:14px}
#stop:active{background:#000;color:#fff;outline:3px solid #fff}
</style></head><body>
<div id="status">READY</div>
<div id="pads">
  <div class="pad"><div class="label">Drive</div>
    <div class="track" id="drive"><div class="knob"></div></div></div>
  <div class="pad"><div class="label">Steer</div>
    <div class="track" id="steer"><div class="knob"></div></div></div>
</div>
<button id="stop">STOP</button>
<script>
const statusEl=document.getElementById('status');
const cmd={x:0,y:0};
let lastSend=0;

function send(force){
  const now=performance.now();
  if(!force && now-lastSend<80) return;
  lastSend=now;
  fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(cmd)})
   .then(()=>{statusEl.textContent=`DRIVE ${cmd.y.toFixed(2)}   STEER ${cmd.x.toFixed(2)}`;})
   .catch(e=>{statusEl.textContent='ERROR: '+e;});
}

// One-axis stick. axis 'y' = drive (up is +), axis 'x' = steer (right is +).
function stick(id,axis,key){
  const el=document.getElementById(id), knob=el.querySelector('.knob');
  let pid=null;
  function move(ev){
    const r=el.getBoundingClientRect();
    const half=(axis==='y'?r.height:r.width)/2-35;
    let d=axis==='y' ? ev.clientY-(r.top+r.height/2) : ev.clientX-(r.left+r.width/2);
    d=Math.max(-half,Math.min(half,d));
    knob.style.transform=axis==='y'?`translateY(${d}px)`:`translateX(${d}px)`;
    cmd[key]=axis==='y' ? -d/half : d/half;
    send(false);
  }
  function release(ev){
    if(ev.pointerId!==pid) return;
    pid=null; el.classList.remove('active');
    knob.style.transform='none'; cmd[key]=0; send(true);
  }
  el.addEventListener('pointerdown',e=>{
    if(pid!==null) return;
    pid=e.pointerId; el.setPointerCapture(pid); el.classList.add('active'); move(e);});
  el.addEventListener('pointermove',e=>{if(e.pointerId===pid) move(e);});
  el.addEventListener('pointerup',release);
  el.addEventListener('pointercancel',release);
}
stick('drive','y','y');
stick('steer','x','x');

// Board stops the motors if it hears nothing for 500 ms, so keep resending while held.
setInterval(()=>{ if(cmd.x||cmd.y) send(true); },150);

document.getElementById('stop').addEventListener('click',()=>{
  cmd.x=0; cmd.y=0;
  document.querySelectorAll('.knob').forEach(k=>k.style.transform='none');
  fetch('/stop',{method:'POST'}); statusEl.textContent='STOPPED';
});
</script></body></html>"""

if __name__ == "__main__":
    print("Open http://<this-pc-ip>:%d from your phone" % HTTP_PORT)
    app.run(host="0.0.0.0", port=HTTP_PORT, debug=False, threaded=True)
