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

- **Train mode:** point the camera around and click the box you'd steer toward. You can also press `1`–`9` and `0` (box 10), or `B` for back. Each press saves one labeled example. `Space` turns on continuous recording, which keeps saving every frame under the last box you picked.
- **Train model:** fits the classifier and reports held-out accuracy.
- **Drive mode:** the model picks the box. The output can be Print, Keys, or Serial.

| Output | What it sends |
|---|---|
| Print | box name to the console when it changes |
| Keys (WASD) | boxes 1–2 → `A`, 3–4 → `W+A`, 5–6 → `W`, 7–8 → `W+D`, 9–10 → `D`, BACK → `S` |
| Serial | one byte on change: `0`–`9` for boxes 1–10, `B` for back, `S` for stop |

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
- **These numbers are likely optimistic.** Continuous recording saves many nearly identical frames in a row, and a random split puts some of them in both training and test sets. A fairer test is to record a separate session in a different room and score the model on that.

## Limitations and next steps

- Relative depth only. It can't say "stop at 30 cm", so keep a bump sensor or ultrasonic sensor as a safety stop.
- The training data is indoor only. Outdoor or lunar-style terrain will need its own examples.
- **Next:** a UDP output so the trainer drives a Dirtlet over Wi-Fi like `joystick_server.py`; a test session recorded separately for honest accuracy; more examples for boxes 2 and 6.

## Files

| File | Purpose |
|---|---|
| `depth_nav.py` | depth model wrapper, rule-based planner, outputs, command-line runner |
| `trainer_gui.py` | PySide6 trainer and driver GUI |
| `data/dataset.npz` | recorded training data |
| `data/model.joblib` | trained model (not committed; retrain from the dataset with **Train model**) |
