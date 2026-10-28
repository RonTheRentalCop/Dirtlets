# Citation: AI-assisted code generation - Claude (Anthropic, 2026).
# AI help was limited to small scripting mistakes and troubleshooting
# while fixing shorted electronics. The code and design are my own.

import argparse
import threading
import time

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import pipeline

MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"


class FrameSource:

    def __init__(self, source):
        self.source = int(source) if str(source).isdigit() else str(source)
        self.is_stream = isinstance(self.source, str)
        self.frame, self.stamp = None, 0.0
        self.lock = threading.Lock()
        self.fresh = threading.Event()
        self.cap = self._open()
        self.ok = self.cap.isOpened()
        self.running = self.ok
        self.thread = threading.Thread(target=self._loop, daemon=True)
        if self.ok:
            self.thread.start()

    def _open(self):
        cap = cv2.VideoCapture(self.source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

    def _loop(self):
        failures = 0
        while self.running:
            ok, frame = self.cap.read()
            if ok:
                failures = 0
                with self.lock:
                    self.frame, self.stamp = frame, time.time()
                self.fresh.set()
                continue
            failures += 1
            time.sleep(0.05)
            if self.is_stream and failures >= 20:
                self.cap.release()
                self.cap = self._open()
                failures = 0

    def read(self, timeout=1.0):
        if not self.fresh.wait(timeout):
            return None
        with self.lock:
            self.fresh.clear()
            return self.frame

    def close(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(2)
        self.cap.release()


class DepthEstimator:
    def __init__(self, model_id=MODEL_ID):
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
        print(f"Loading {model_id} on {device}...")
        self.pipe = pipeline("depth-estimation", model=model_id, device=device)

    def __call__(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        out = self.pipe(Image.fromarray(rgb))
        d = out["predicted_depth"].squeeze().float().cpu().numpy()
        d = cv2.resize(d, (frame_bgr.shape[1], frame_bgr.shape[0]))
        lo, hi = np.percentile(d, 2), np.percentile(d, 98)
        return np.clip((d - lo) / (hi - lo + 1e-6), 0, 1)


class Planner:

    def __init__(self, columns=5, block_threshold=0.75, smoothing=0.85, forward_bias=0.08,
                 switch_margin=0.08, hold_frames=4):
        self.columns = columns
        self.forward_bias = forward_bias
        self.switch_margin = switch_margin
        self.block_threshold = block_threshold
        self.smoothing = smoothing
        self.scores = None
        self.current = columns // 2
        self.debounce = Debouncer(hold_frames)

    def plan(self, closeness):
        h, w = closeness.shape
        band = closeness[int(h * 0.25): int(h * 0.85)]
        cols = np.array_split(band, self.columns, axis=1)
        nearest = np.array([np.percentile(c, 90) for c in cols])
        scores = 1.0 - nearest

        if self.scores is None:
            self.scores = scores
        else:
            self.scores = self.smoothing * self.scores + (1 - self.smoothing) * scores

        best = int(np.argmax(self.scores))
        center = self.columns // 2
        if self.scores[center] >= self.scores[best] - self.forward_bias:
            best = center
        if self.scores[self.current] >= self.scores[best] - self.switch_margin:
            best = self.current
        self.current = best
        if self.scores[best] < 1 - self.block_threshold:
            command = "back"
        elif best < center:
            command = "left"
        elif best > center:
            command = "right"
        else:
            command = "forward"
        return self.debounce(command), best, self.scores


class Debouncer:

    def __init__(self, hold=4):
        self.hold = hold
        self.value = None
        self.candidate = None
        self.count = 0

    def __call__(self, value):
        if self.value is None or value == self.value:
            self.value, self.candidate, self.count = value, None, 0
        elif value == self.candidate:
            self.count += 1
            if self.count >= self.hold:
                self.value, self.candidate, self.count = value, None, 0
        else:
            self.candidate, self.count = value, 1
        return self.value


class PrintOutput:
    def __init__(self):
        self.last = None

    def send(self, command):
        if command != self.last:
            print(f"-> {command}")
            self.last = command

    def close(self):
        pass


class KeyOutput:
    KEYS = {"forward": "w", "left": "a", "right": "d", "back": "s"}

    def __init__(self):
        from pynput.keyboard import Controller
        self.kb = Controller()
        self.held = None

    def send(self, command):
        key = self.KEYS.get(command)
        if key == self.held:
            return
        if self.held:
            self.kb.release(self.held)
        if key:
            self.kb.press(key)
        self.held = key

    def close(self):
        if self.held:
            self.kb.release(self.held)


class SerialOutput:
    CODES = {"forward": b"F", "left": b"L", "right": b"R", "back": b"B", "stop": b"S"}

    def __init__(self, port, baud):
        import serial
        self.ser = serial.Serial(port, baud, timeout=0)
        self.last = None

    def send(self, command):
        if command != self.last:
            self.ser.write(self.CODES[command])
            self.last = command

    def close(self):
        self.ser.write(self.CODES["stop"])
        self.ser.close()


def draw_overlay(closeness, command, best, scores):
    vis = cv2.applyColorMap((closeness * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    h, w = vis.shape[:2]
    n = len(scores)
    for i, s in enumerate(scores):
        x0, x1 = int(i * w / n), int((i + 1) * w / n)
        color = (0, 255, 0) if i == best else (200, 200, 200)
        cv2.rectangle(vis, (x0, int(h * 0.25)), (x1 - 1, int(h * 0.85)), color, 2 if i == best else 1)
        cv2.putText(vis, f"{s:.2f}", (x0 + 5, int(h * 0.25) - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    cv2.putText(vis, command.upper(), (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    return vis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", default="0", help="webcam index, or a stream URL like http://<cam-ip>:81/stream")
    ap.add_argument("--columns", type=int, default=5, help="odd number works best")
    ap.add_argument("--block-threshold", type=float, default=0.75)
    ap.add_argument("--output", choices=["print", "keys", "serial"], default="print")
    ap.add_argument("--port", help="serial port for --output serial")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--width", type=int, default=518, help="processing width (smaller = faster)")
    args = ap.parse_args()

    if args.output == "keys":
        out = KeyOutput()
        print("Key output: starting in 3s, focus the target window...")
        time.sleep(3)
    elif args.output == "serial":
        if not args.port:
            ap.error("--port is required for serial output")
        out = SerialOutput(args.port, args.baud)
    else:
        out = PrintOutput()

    depth = DepthEstimator()
    planner = Planner(args.columns, args.block_threshold)
    cap = FrameSource(args.camera)
    if not cap.ok:
        raise SystemExit(f"Could not open camera {args.camera} (check macOS camera permission for your "
                         f"terminal, or that the ESP32-CAM is on the same Wi-Fi)")

    try:
        t_prev = time.time()
        while True:
            frame = cap.read()
            if frame is None:
                print("No frames from camera...")
                continue
            scale = args.width / frame.shape[1]
            frame = cv2.resize(frame, None, fx=scale, fy=scale)

            closeness = depth(frame)
            command, best, scores = planner.plan(closeness)
            out.send(command)

            now = time.time()
            fps = 1 / max(now - t_prev, 1e-6)
            t_prev = now
            vis = draw_overlay(closeness, command, best, scores)
            cv2.putText(vis, f"{fps:.1f} fps", (vis.shape[1] - 110, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.imshow("camera", frame)
            cv2.imshow("depth (bright = close)", vis)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        out.close()
        cap.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
