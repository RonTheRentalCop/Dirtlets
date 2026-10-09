"""
Depth navigation trainer.

Teach the navigator by example: while the camera runs, click (or press) the box
you would steer toward. Each click saves the current depth map with that label.
Hit "Train model", then switch to Drive and it picks boxes on its own.

Boxes 1-10 are steering directions, far left to far right. BACK means reverse.

Keyboard:  1-9, 0 (=10) pick a box   B = back   Space = toggle continuous recording

Run from Terminal.app (it needs camera permission):
    .venv/bin/python trainer_gui.py
"""

import sys
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
    QVBoxLayout, QWidget,
)

from depth_nav import Debouncer, DepthEstimator

N_BOXES = 10
SMOOTHING = 0.85  # how much each frame keeps from previous frames (higher = steadier, slower)
HOLD_FRAMES = 4   # a new direction must win this many frames in a row before it's used
BACK = N_BOXES  # class index for the backwards box
LABELS = [str(i + 1) for i in range(N_BOXES)] + ["BACK"]

DATA_DIR = Path(__file__).parent / "data"
DATASET_PATH = DATA_DIR / "dataset.npz"
MODEL_PATH = DATA_DIR / "model.joblib"

BAND = (0.25, 0.85)  # vertical slice of the frame used for steering
GRID = (20, 12)      # depth map is shrunk to this many cells for the model


def box_color(i):
    if i == BACK:
        return QColor("#e5484d")
    # Rainbow from blue (far left) through green to orange (far right)
    return QColor.fromHsv(int(220 - i * 22), 190, 235)


# ---------------------------------------------------------------- features

def column_scores(closeness):
    """How open each of the 10 columns is: 1 = far / clear, 0 = something close."""
    h = closeness.shape[0]
    band = closeness[int(h * BAND[0]): int(h * BAND[1])]
    cols = np.array_split(band, N_BOXES, axis=1)
    return np.array([1.0 - np.percentile(c, 90) for c in cols], dtype=np.float32)


def features(closeness):
    small = cv2.resize(closeness, GRID, interpolation=cv2.INTER_AREA).ravel()
    return np.concatenate([small, column_scores(closeness)]).astype(np.float32)


def rule_based_choice(scores, block=0.25, forward_bias=0.05):
    """Fallback before a model is trained: head for the most open column."""
    best = int(np.argmax(scores))
    if scores[best] < block:
        return BACK
    center = [N_BOXES // 2 - 1, N_BOXES // 2]
    c = max(center, key=lambda i: scores[i])
    if scores[c] >= scores[best] - forward_bias:
        return c
    return best


# ---------------------------------------------------------------- outputs

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
    """Holds W/A/S/D combos: outer boxes turn in place, inner boxes turn while moving."""
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
    """Sends one byte when the choice changes: '0'-'9' for boxes 1-10, 'B' back, 'S' stop."""

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


# ---------------------------------------------------------------- camera + depth thread

class DepthWorker(QThread):
    frame_ready = Signal(object, object)  # (rgb frame, closeness map)
    status = Signal(str)

    def __init__(self, camera=0, width=518):
        super().__init__()
        self.camera, self.width = camera, width
        self.running = True

    def run(self):
        self.status.emit("Loading depth model...")
        depth = DepthEstimator()
        cap = cv2.VideoCapture(self.camera)
        if not cap.isOpened():
            self.status.emit("Camera not available. Allow camera access for Terminal in "
                             "System Settings > Privacy & Security > Camera, then restart.")
            return
        self.status.emit("Running")
        while self.running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.05)
                continue
            scale = self.width / frame.shape[1]
            frame = cv2.resize(frame, None, fx=scale, fy=scale)
            closeness = depth(frame)
            self.frame_ready.emit(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), closeness)
        cap.release()

    def stop(self):
        self.running = False
        self.wait(3000)


# ---------------------------------------------------------------- GUI

def to_pixmap(rgb):
    h, w = rgb.shape[:2]
    img = QImage(np.ascontiguousarray(rgb).data, w, h, 3 * w, QImage.Format_RGB888)
    return QPixmap.fromImage(img.copy())


class TrainerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Depth Nav Trainer")
        self.X, self.y = self.load_dataset()
        self.model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
        self.latest = None        # latest closeness map
        self.selected = None      # label being recorded / predicted
        self.output = None
        self.smooth, self.current, self.debounce = None, None, Debouncer(HOLD_FRAMES)
        self.t_prev = time.time()

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        # --- video views
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

        # --- the 10 navigation boxes + back
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
                grid.addWidget(b, 1, 3, 1, 4)  # BACK centered underneath
        layout.addLayout(grid)

        # --- controls
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
        self.output_combo.addItems(["Print", "Keys (WASD)", "Serial"])
        self.output_combo.setFocusPolicy(Qt.NoFocus)
        controls.addWidget(self.output_combo)
        self.port_edit = QLineEdit(placeholderText="/dev/tty.usbserial-...")
        self.port_edit.setFixedWidth(170)
        controls.addWidget(self.port_edit)
        layout.addLayout(controls)

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

        self.worker = DepthWorker()
        self.worker.frame_ready.connect(self.on_frame)
        self.worker.status.connect(self.set_status)
        self.worker.start()

    # ---------- data

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
            acc = make().fit(Xtr, ytr).score(Xte, yte)
            acc_text = f"  Held-out accuracy: {acc:.0%}"

        self.model = make().fit(X, y)
        DATA_DIR.mkdir(exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)
        self.save_dataset()
        self.set_status(f"Model trained on {len(y)} samples.{acc_text}")

    # ---------- interaction

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
                    self.output = SerialOutput(self.port_edit.text().strip())
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
        self.port_edit.setEnabled(not driving)
        self.refresh_boxes()

    # ---------- frames

    def on_frame(self, rgb, closeness):
        self.latest = closeness
        scores = column_scores(closeness)

        if self.drive_radio.isChecked():
            if self.model is not None:
                # Average the model's confidence over recent frames instead of trusting one frame.
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
                self.output.send(self.selected)
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
        # TURBO colormap: blue = far, green/yellow = middle, red = close
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

    # ---------- display

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
        self.worker.stop()
        if self.output:
            self.output.close()
        self.save_dataset()
        super().closeEvent(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TrainerWindow()
    win.resize(1100, 680)
    win.show()
    sys.exit(app.exec())
