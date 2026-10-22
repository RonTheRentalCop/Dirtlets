# Citation: AI-assisted code generation - Claude (Anthropic, 2026).
# AI help was limited to small scripting mistakes and troubleshooting
# while fixing shorted electronics. The code and design are my own.

import argparse
import socket
import sys
import threading
import time
from pathlib import Path

import cv2
import joblib
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QRadioButton,
    QSlider, QVBoxLayout, QWidget,
)

from depth_nav import Debouncer, DepthEstimator, FrameSource

N_BOXES = 10
SMOOTHING = 0.85
HOLD_FRAMES = 4
BACK = N_BOXES
LABELS = [str(i + 1) for i in range(N_BOXES)] + ["BACK"]

DATA_DIR = Path(__file__).parent / "data"
DATASET_PATH = DATA_DIR / "dataset.npz"
MODEL_PATH = DATA_DIR / "model.joblib"

BAND = (0.25, 0.85)
GRID = (20, 12)


def box_color(i):
    if i == BACK:
        return QColor("#e5484d")
    return QColor.fromHsv(int(220 - i * 22), 190, 235)


def column_scores(closeness):
    h = closeness.shape[0]
    band = closeness[int(h * BAND[0]): int(h * BAND[1])]
    cols = np.array_split(band, N_BOXES, axis=1)
    return np.array([1.0 - np.percentile(c, 90) for c in cols], dtype=np.float32)


def features(closeness):
    small = cv2.resize(closeness, GRID, interpolation=cv2.INTER_AREA).ravel()
    return np.concatenate([small, column_scores(closeness)]).astype(np.float32)


def mirror(X, y):
    cells = GRID[0] * GRID[1]
    grid = X[:, :cells].reshape(-1, GRID[1], GRID[0])[:, :, ::-1].reshape(-1, cells)
    cols = X[:, cells:][:, ::-1]
    y_m = np.where(y == BACK, BACK, N_BOXES - 1 - y)
    return np.hstack([grid, cols]), y_m


def with_mirrored(X, y):
    Xm, ym = mirror(X, y)
    return np.vstack([X, Xm]), np.concatenate([y, ym])


def rule_based_choice(scores, block=0.25, forward_bias=0.05):
    best = int(np.argmax(scores))
    if scores[best] < block:
        return BACK
    center = [N_BOXES // 2 - 1, N_BOXES // 2]
    c = max(center, key=lambda i: scores[i])
    if scores[c] >= scores[best] - forward_bias:
        return c
    return best


class Output:
    def send(self, choice): ...
    def close(self): ...


class PrintOutput(Output):
    def __init__(self):
        self.last = None

    def send(self, choice):
        if choice != self.last:
            print(f"-> {LABELS[choice] if choice is not None else 'STOP'}")
            self.last = choice


class KeyOutput(Output):
    KEYMAP = {0: {"a"}, 1: {"a"}, 2: {"w", "a"}, 3: {"w", "a"}, 4: {"w"}, 5: {"w"},
              6: {"w", "d"}, 7: {"w", "d"}, 8: {"d"}, 9: {"d"}, BACK: {"s"}}

    def __init__(self):
        from pynput.keyboard import Controller
        self.kb = Controller()
        self.held = set()

    def send(self, choice):
        want = self.KEYMAP.get(choice, set())
        for k in self.held - want:
            self.kb.release(k)
        for k in want - self.held:
            self.kb.press(k)
        self.held = set(want)

    def close(self):
        self.send(None)


class SerialOutput(Output):

    def __init__(self, port, baud=115200):
        import serial
        self.ser = serial.Serial(port, baud, timeout=0)
        self.last = None

    def send(self, choice):
        if choice != self.last:
            code = b"S" if choice is None else b"B" if choice == BACK else str(choice).encode()
            self.ser.write(code)
            self.last = choice

    def close(self):
        self.ser.write(b"S")
        self.ser.close()


def box_to_drive(choice, speed, max_steer):
    if choice == BACK:
        return -speed, 0
    t = (choice - (N_BOXES - 1) / 2) / ((N_BOXES - 1) / 2)
    return round(speed * (1 - 0.4 * abs(t))), round(t * max_steer)


class UdpOutput(Output):
    PORT = 3333
    RATE_HZ = 10
    STALE_S = 0.3

    def __init__(self, host, speed=150, max_steer=300):
        if not host:
            raise ValueError("Enter the motor board's IP address")
        self.addr = (socket.gethostbyname(host), self.PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.speed, self.max_steer = speed, max_steer
        self.choice, self.updated = None, 0.0
        self.lock = threading.Lock()
        self.running = True
        self.last_message = ""
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def send(self, choice):
        with self.lock:
            self.choice, self.updated = choice, time.time()

    def message(self):
        with self.lock:
            choice, age = self.choice, time.time() - self.updated
        if choice is None or age > self.STALE_S:
            return "STOP"
        drive, steer = box_to_drive(choice, self.speed, self.max_steer)
        return f"DRIVE {drive} {steer}"

    def _loop(self):
        while self.running:
            self.last_message = self.message()
            self.sock.sendto(self.last_message.encode("ascii"), self.addr)
            time.sleep(1 / self.RATE_HZ)

    def close(self):
        self.running = False
        self.thread.join(1)
        for _ in range(3):
            self.sock.sendto(b"STOP", self.addr)
        self.sock.close()


class DepthWorker(QThread):
    frame_ready = Signal(object, object)
    status = Signal(str)

    estimator = None

    def __init__(self, camera="0", width=518):
        super().__init__()
        self.camera, self.width = camera, width
        self.running = True

    def run(self):
        if DepthWorker.estimator is None:
            self.status.emit("Loading depth model...")
            DepthWorker.estimator = DepthEstimator()
        self.status.emit(f"Connecting to camera {self.camera}...")
        cap = FrameSource(self.camera)
        if not cap.ok:
            if cap.is_stream:
                self.status.emit(f"Can't reach {self.camera}. Is the ESP32-CAM powered and on the same Wi-Fi?")
            else:
                self.status.emit("Camera not available. Allow camera access for Terminal in "
                                 "System Settings > Privacy & Security > Camera, then restart.")
            return
        self.status.emit(f"Running on camera {self.camera}")
        waiting = False
        while self.running:
            frame = cap.read(timeout=0.5)
            if frame is None:
                if not waiting:
                    self.status.emit("No video from camera, waiting (robot is sent STOP)...")
                waiting = True
                continue
            if waiting:
                self.status.emit(f"Running on camera {self.camera}")
                waiting = False
            scale = self.width / frame.shape[1]
            frame = cv2.resize(frame, None, fx=scale, fy=scale)
            closeness = DepthWorker.estimator(frame)
            self.frame_ready.emit(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), closeness)
        cap.close()

    def stop(self):
        self.running = False
        self.wait(3000)


def to_pixmap(rgb):
    h, w = rgb.shape[:2]
    img = QImage(np.ascontiguousarray(rgb).data, w, h, 3 * w, QImage.Format_RGB888)
    return QPixmap.fromImage(img.copy())


class TrainerWindow(QMainWindow):
    def __init__(self, camera="0"):
        super().__init__()
        self.setWindowTitle("Depth Nav Trainer")
        self.X, self.y = self.load_dataset()
        self.model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
        self.latest = None
        self.selected = None
        self.output = None
        self.stopped = False
        self.smooth, self.current, self.debounce = None, None, Debouncer(HOLD_FRAMES)
        self.t_prev = time.time()

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Camera:"))
        self.camera_edit = QLineEdit(camera, placeholderText="0  or  http://<cam-ip>:81/stream")
        self.camera_edit.returnPressed.connect(self.connect_camera)
        source_row.addWidget(self.camera_edit, 1)
        connect_btn = QPushButton("Connect")
        connect_btn.setFocusPolicy(Qt.NoFocus)
        connect_btn.clicked.connect(self.connect_camera)
        source_row.addWidget(connect_btn)
        layout.addLayout(source_row)

        views = QHBoxLayout()
        self.cam_view = QLabel(alignment=Qt.AlignCenter)
        self.depth_view = QLabel(alignment=Qt.AlignCenter)
        for v, title in ((self.cam_view, "Camera"), (self.depth_view, "Depth  (red = close, blue = far)")):
            col = QVBoxLayout()
            col.addWidget(QLabel(f"<b>{title}</b>"))
            v.setMinimumSize(480, 340)
            v.setStyleSheet("background:#111; border-radius:8px;")
            col.addWidget(v)
            views.addLayout(col)
        layout.addLayout(views)

        grid = QGridLayout()
        self.boxes = []
        for i in range(N_BOXES + 1):
            b = QPushButton()
            b.setFocusPolicy(Qt.NoFocus)
            b.setMinimumHeight(64)
            b.clicked.connect(lambda _, i=i: self.choose(i))
            self.boxes.append(b)
            if i < N_BOXES:
                grid.addWidget(b, 0, i)
            else:
                grid.addWidget(b, 1, 3, 1, 4)
        layout.addLayout(grid)

        controls = QHBoxLayout()
        self.train_radio = QRadioButton("Train")
        self.drive_radio = QRadioButton("Drive")
        self.train_radio.setChecked(True)
        mode_group = QButtonGroup(self)
        for r in (self.train_radio, self.drive_radio):
            r.setFocusPolicy(Qt.NoFocus)
            mode_group.addButton(r)
            controls.addWidget(r)
        self.drive_radio.toggled.connect(self.mode_changed)

        self.continuous = QCheckBox("Continuous record (Space)")
        self.continuous.setFocusPolicy(Qt.NoFocus)
        controls.addWidget(self.continuous)

        for text, slot in (("Train model", self.train_model), ("Undo last", self.undo),
                           ("Clear data", self.clear_data)):
            b = QPushButton(text)
            b.setFocusPolicy(Qt.NoFocus)
            b.clicked.connect(slot)
            controls.addWidget(b)

        controls.addStretch()
        controls.addWidget(QLabel("Output:"))
        self.output_combo = QComboBox()
        self.output_combo.addItems(["Print", "Keys (WASD)", "Serial", "UDP (Dirtlet)"])
        self.output_combo.setFocusPolicy(Qt.NoFocus)
        self.output_combo.currentIndexChanged.connect(self.output_kind_changed)
        controls.addWidget(self.output_combo)
        self.target_edit = QLineEdit()
        self.target_edit.setFixedWidth(170)
        controls.addWidget(self.target_edit)
        layout.addLayout(controls)

        safety = QHBoxLayout()
        safety.addWidget(QLabel("Robot speed:"))
        self.speed_slider = QSlider(Qt.Horizontal, minimum=0, maximum=300, value=150)
        self.speed_slider.setFocusPolicy(Qt.NoFocus)
        self.speed_slider.valueChanged.connect(self.speed_changed)
        safety.addWidget(self.speed_slider, 1)
        self.speed_label = QLabel()
        self.speed_label.setFixedWidth(110)
        safety.addWidget(self.speed_label)
        self.stop_btn = QPushButton()
        self.stop_btn.setFocusPolicy(Qt.NoFocus)
        self.stop_btn.setMinimumSize(200, 44)
        self.stop_btn.clicked.connect(self.toggle_stop)
        safety.addWidget(self.stop_btn)
        layout.addLayout(safety)
        self.speed_changed(self.speed_slider.value())
        self.output_kind_changed(0)
        self.refresh_stop()

        self.status = QLabel()
        layout.addWidget(self.status)

        self.setStyleSheet("""
            QMainWindow, QWidget { background:#1b1d23; color:#e8e8ea; font-size:13px; }
            QPushButton { background:#2c2f38; border:1px solid #3a3e4a; border-radius:6px; padding:6px 10px; }
            QPushButton:hover { background:#363a45; }
            QLineEdit, QComboBox { background:#2c2f38; border:1px solid #3a3e4a; border-radius:6px; padding:4px; }
        """)
        self.refresh_boxes()
        self.set_status("Starting camera...")

        self.worker = None
        self.connect_camera()


    def connect_camera(self):
        if self.worker:
            self.worker.stop()
        self.worker = DepthWorker(self.camera_edit.text().strip() or "0")
        self.worker.frame_ready.connect(self.on_frame)
        self.worker.status.connect(self.set_status)
        self.worker.start()

    def output_kind_changed(self, idx):
        hints = {2: "/dev/tty.usbserial-...", 3: "motor board IP, e.g. 192.168.1.50"}
        self.target_edit.setPlaceholderText(hints.get(idx, ""))
        self.target_edit.setEnabled(idx in hints)

    def speed_changed(self, value):
        self.speed_label.setText(f"{value} / 1000")
        if isinstance(self.output, UdpOutput):
            self.output.speed = value

    def toggle_stop(self):
        self.stopped = not self.stopped
        if self.output:
            self.output.send(None)
        self.refresh_stop()

    def refresh_stop(self):
        if self.stopped:
            self.stop_btn.setText("STOPPED  (Esc to resume)")
            self.stop_btn.setStyleSheet("QPushButton { background:#8a6d00; color:white; font-weight:bold;"
                                        " font-size:15px; border-radius:8px; }")
        else:
            self.stop_btn.setText("STOP  (Esc)")
            self.stop_btn.setStyleSheet("QPushButton { background:#c62828; color:white; font-weight:bold;"
                                        " font-size:16px; border-radius:8px; }")


    def load_dataset(self):
        if DATASET_PATH.exists():
            d = np.load(DATASET_PATH)
            return list(d["X"]), list(d["y"])
        return [], []

    def save_dataset(self):
        DATA_DIR.mkdir(exist_ok=True)
        if self.X:
            np.savez_compressed(DATASET_PATH, X=np.array(self.X), y=np.array(self.y))
        elif DATASET_PATH.exists():
            DATASET_PATH.unlink()

    def record(self, label):
        if self.latest is None:
            return
        self.X.append(features(self.latest))
        self.y.append(label)
        self.refresh_boxes()

    def undo(self):
        if self.X:
            self.X.pop()
            self.y.pop()
            self.save_dataset()
            self.refresh_boxes()

    def clear_data(self):
        if QMessageBox.question(self, "Clear data", "Delete all recorded samples?") == QMessageBox.Yes:
            self.X, self.y = [], []
            self.save_dataset()
            self.refresh_boxes()

    def train_model(self):
        from sklearn.model_selection import train_test_split
        from sklearn.neural_network import MLPClassifier
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        X, y = np.array(self.X), np.array(self.y)
        if len(set(y)) < 2 or len(y) < 10:
            QMessageBox.information(self, "Need more data",
                                    "Record at least 10 samples across 2 or more boxes first.")
            return
        self.set_status("Training...")
        QApplication.processEvents()

        def make():
            return make_pipeline(StandardScaler(),
                                 MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=600,
                                               early_stopping=len(y) >= 50, random_state=0))

        acc_text = ""
        counts = np.bincount(y)
        if len(y) >= 30 and counts[counts > 0].min() >= 2:
            Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
            acc = make().fit(*with_mirrored(Xtr, ytr)).score(Xte, yte)
            acc_text = f"  Held-out accuracy: {acc:.0%}"

        self.model = make().fit(*with_mirrored(X, y))
        DATA_DIR.mkdir(exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)
        self.save_dataset()
        self.set_status(f"Model trained on {len(y)} samples + {len(y)} mirrored.{acc_text}")


    def choose(self, label):
        self.selected = label
        if self.train_radio.isChecked():
            self.record(label)
            self.save_dataset()
        self.refresh_boxes()

    def keyPressEvent(self, e):
        key = e.text().lower()
        if key.isdigit():
            self.choose(int(key) - 1 if key != "0" else 9)
        elif key == "b":
            self.choose(BACK)
        elif e.key() == Qt.Key_Space:
            self.continuous.toggle()
        elif e.key() == Qt.Key_Escape:
            self.toggle_stop()
        else:
            super().keyPressEvent(e)

    def mode_changed(self, driving):
        self.smooth, self.current, self.debounce = None, None, Debouncer(HOLD_FRAMES)
        if driving:
            try:
                idx = self.output_combo.currentIndex()
                if idx == 1:
                    self.output = KeyOutput()
                elif idx == 2:
                    self.output = SerialOutput(self.target_edit.text().strip())
                elif idx == 3:
                    self.output = UdpOutput(self.target_edit.text().strip(), speed=self.speed_slider.value())
                else:
                    self.output = PrintOutput()
            except Exception as ex:
                QMessageBox.warning(self, "Output error", str(ex))
                self.train_radio.setChecked(True)
                return
            self.continuous.setChecked(False)
            src = "trained model" if self.model else "built-in rule (no model trained yet)"
            self.set_status(f"Driving with {src}")
        else:
            if self.output:
                self.output.close()
                self.output = None
            self.selected = None
            self.set_status("Training mode")
        self.output_combo.setEnabled(not driving)
        self.target_edit.setEnabled(not driving and self.output_combo.currentIndex() in (2, 3))
        self.refresh_boxes()


    def on_frame(self, rgb, closeness):
        self.latest = closeness
        scores = column_scores(closeness)

        if self.drive_radio.isChecked():
            if self.model is not None:
                proba = np.zeros(N_BOXES + 1)
                proba[self.model.classes_] = self.model.predict_proba(features(closeness)[None])[0]
                self.smooth = proba if self.smooth is None else SMOOTHING * self.smooth + (1 - SMOOTHING) * proba
                choice = int(np.argmax(self.smooth))
                if self.current is not None and self.smooth[self.current] >= self.smooth[choice] - 0.1:
                    choice = self.current
            else:
                self.smooth = scores if self.smooth is None else SMOOTHING * self.smooth + (1 - SMOOTHING) * scores
                choice = rule_based_choice(self.smooth)
                if (self.current is not None and self.current != BACK and choice != BACK
                        and self.smooth[self.current] >= self.smooth[choice] - 0.08):
                    choice = self.current
            self.current = choice
            self.selected = self.debounce(choice)
            if self.output:
                self.output.send(None if self.stopped else self.selected)
            self.refresh_boxes()
        elif self.continuous.isChecked() and self.selected is not None:
            self.record(self.selected)

        now = time.time()
        fps = 1 / max(now - self.t_prev, 1e-6)
        self.t_prev = now

        self.cam_view.setPixmap(to_pixmap(rgb).scaled(
            self.cam_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.depth_view.setPixmap(to_pixmap(self.draw_depth(closeness, scores, fps)).scaled(
            self.depth_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def draw_depth(self, closeness, scores, fps):
        vis = cv2.applyColorMap((closeness * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
        vis = cv2.cvtColor(vis, cv2.COLOR_BGR2RGB)
        h, w = vis.shape[:2]
        y0, y1 = int(h * BAND[0]), int(h * BAND[1])
        for i, s in enumerate(scores):
            x0, x1 = int(i * w / N_BOXES), int((i + 1) * w / N_BOXES)
            on = i == self.selected
            color = (255, 255, 255) if on else (230, 230, 230)
            cv2.rectangle(vis, (x0, y0), (x1 - 1, y1), color, 3 if on else 1)
            cv2.putText(vis, str(i + 1), (x0 + 4, y0 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        if self.selected == BACK:
            cv2.putText(vis, "BACK", (w // 2 - 40, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(vis, f"{fps:.1f} fps", (w - 90, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return vis


    def refresh_boxes(self):
        counts = np.bincount(np.array(self.y, dtype=int), minlength=N_BOXES + 1) if self.y else [0] * (N_BOXES + 1)
        for i, b in enumerate(self.boxes):
            c = box_color(i)
            on = i == self.selected
            bg = c.lighter(115).name() if on else c.darker(170).name()
            border = "3px solid white" if on else f"2px solid {c.name()}"
            b.setText(f"{LABELS[i]}\n{counts[i]} samples")
            b.setStyleSheet(f"QPushButton {{ background:{bg}; border:{border}; border-radius:10px;"
                            f" color:{'#111' if on else 'white'}; font-size:15px; font-weight:bold; }}")

    def set_status(self, text):
        model = "model: trained" if self.model else "model: none"
        self.status.setText(f"{text}    |    {len(self.y)} samples    |    {model}")

    def closeEvent(self, e):
        if self.output:
            self.output.close()
        if self.worker:
            self.worker.stop()
        self.save_dataset()
        super().closeEvent(e)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", default="0", help="webcam index, or the ESP32-CAM URL http://<cam-ip>:81/stream")
    args = ap.parse_args()
    app = QApplication(sys.argv[:1])
    win = TrainerWindow(args.camera)
    win.resize(1100, 680)
    win.show()
    sys.exit(app.exec())
