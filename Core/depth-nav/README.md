# Depth Nav

Camera-only obstacle avoidance for the Dirtlets. A normal camera feeds an AI depth model, which estimates what's close and what's far. The robot then steers toward the most open, farthest area. No lidar or depth sensor needed.

You can run it two ways:

- **Rule-based** (`depth_nav.py`): head for the most open column. No training.
- **Learned** (`trainer_gui.py`): drive by example in a GUI, then train a small neural network to copy your choices.

## How it works

```
camera frame ──► Depth Anything V2 (Small) ──► depth map ──► 10 columns + BACK ──► command
                 pretrained, runs on Apple GPU   red = close,    rule or trained     print / WASD keys /
                                                 blue = far      classifier          serial to ESP32
```

1. **Depth estimation.** Each frame goes through [Depth Anything V2 Small](https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf), a pretrained monocular depth model. It outputs *relative* depth, so it can tell nearer from farther, but not exact distances in meters. Each frame's depth map is normalized to 0–1, where 1 is the closest thing in view.
2. **Columns.** The middle band of the frame (25%–85% of the height, which skips ceiling or sky and the floor right in front of the robot) is split into 10 vertical columns. Each column is scored by its *closest* obstacle (90th percentile of closeness). One near object blocks that whole direction.
3. **Decision.** The robot picks one of 11 actions: boxes 1–10 (far left to far right) or BACK.
4. **Stabilizing.** Without this, the choice flips every frame between columns that score almost the same. Three things stop that:
   - smoothing across frames (each frame keeps 85% of the previous value)
   - hysteresis (keep the current direction unless another one is clearly better)
   - debounce (a new direction must win 4 frames in a row)

## Trainer GUI

```bash
cd Core/depth-nav
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python trainer_gui.py
```

Run it from a terminal that has camera permission (System Settings → Privacy & Security → Camera).

**Camera:** the box at the top takes a webcam number (`0`) or the robot's ESP32-CAM stream (`http://<cam-ip>:81/stream`). You can also pass it at startup with `--camera`. Video is read on a background thread that keeps only the newest frame, so a slow model never falls behind, and the stream reconnects by itself if Wi-Fi drops. Setting up the camera board is covered in [firmware/micropython/camera_stream](../../firmware/micropython/camera_stream/README.md).

- **Train mode:** point the camera around and click the box you'd steer toward. You can also press `1`–`9` and `0` (box 10), or `B` for back. Each press saves one labeled example. `Space` turns on continuous recording, which keeps saving every frame under the last box you picked.
- **Train model:** fits the classifier and reports held-out accuracy. Every example is also flipped left-to-right and added to the training data (box 3 ↔ box 8, BACK stays BACK), which doubles it at no cost.
- **Drive mode:** the model picks the box. The output can be Print, Keys, Serial, or UDP.
- **STOP** (red button or `Esc`) sends stop until you press it again. **Robot speed** caps the drive power.

| Output | What it sends |
|---|---|
| Print | box name to the console when it changes |
| Keys (WASD) | boxes 1–2 → `A`, 3–4 → `W+A`, 5–6 → `W`, 7–8 → `W+D`, 9–10 → `D`, BACK → `S` |
| Serial | one byte on change: `0`–`9` for boxes 1–10, `B` for back, `S` for stop |
| UDP (Dirtlet) | `DRIVE <drive> <steer>` to the motor board on port 3333 (same format as `joystick_server.py`), 10 times a second |

**UDP mapping:** steering goes linearly from −300 (box 1) to +300 (box 10). Drive power is the speed slider, reduced by up to 40% in sharp turns. BACK reverses straight. If no new decision arrives for 0.3 s (camera froze, model stalled, Wi-Fi dropped), it sends `STOP` instead of repeating the last command. Closing the window also sends `STOP`.

## Dataset

[`data/dataset.npz`](data/dataset.npz) holds **1,165 labeled examples** recorded indoors with the trainer GUI on a MacBook camera.

```python
import numpy as np
d = np.load("data/dataset.npz")
X, y = d["X"], d["y"]   # X: (1165, 250) float32, y: (1165,) int
```

**Features (250 per example).** These are depth-only. No camera images are stored.

- `X[:, :240]`: the closeness map shrunk to a 20 × 12 grid, flattened row by row (0 = far, 1 = close)
- `X[:, 240:]`: the 10 column openness scores (1 = clear, 0 = blocked)

**Labels:** `0`–`9` mean boxes 1–10 (far left → far right), and `10` means BACK.

| Box | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | BACK |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Examples | 39 | 37 | 115 | 155 | 81 | 13 | 113 | 156 | 150 | 125 | 181 |

## Results

The model is a two-layer neural network (128 → 64 units, scikit-learn `MLPClassifier`) with standardized inputs. It was tested on a random 20% held-out split (233 examples).

| Metric | Result |
|---|---|
| Exact box correct | **85%** |
| Off by at most one box (steering boxes only) | **94%** |
| BACK correct | **100%** (36/36), never confused with a steering box |

What the errors show:

- Most mistakes are **neighboring boxes**, for example 3 vs 4 or 7 vs 8. That's mild for driving, since it means steering slightly more or less.
- **Box 6 is weak** (1 of 3 correct) because it has only 13 examples. Box 2 is also under-recorded.
- **These numbers are optimistic.** Continuous recording saves many nearly identical frames in a row, and a random split puts some of them in both training and test sets.

**A fairer test** trains on the first 80% of examples in recording order and tests on the last 20%, which the model has never seen anything close to:

| | Exact box | Within one box |
|---|---|---|
| Without mirroring | 36% | 85% |
| With mirroring | **41%** | 84% |

So on new footage it usually steers in about the right direction but often misses the exact box. Mirroring helps on new footage. It scores slightly lower on the random split (82% vs 85%), which mostly measures memorizing near-duplicates. More varied recording, especially in different rooms, is what will raise these numbers.

## Limitations and next steps

- Relative depth only. It can't say "stop at 30 cm", so keep a bump sensor or ultrasonic sensor as a safety stop.
- The training data is indoor only. Outdoor or lunar-style terrain will need its own examples.
- The current data was recorded with a laptop camera at desk height. Re-record from the ESP32-CAM mounted on the car, which sees mostly floor.
- **Next:** first drive test over UDP at low speed; record data from the robot's own camera in varied rooms; more examples for boxes 2 and 6.

## Files

| File | Purpose |
|---|---|
| `depth_nav.py` | depth model wrapper, rule-based planner, outputs, command-line runner |
| `trainer_gui.py` | PySide6 trainer and driver GUI |
| `data/dataset.npz` | recorded training data |
| `data/model.joblib` | trained model (not committed; retrain from the dataset with **Train model**) |
