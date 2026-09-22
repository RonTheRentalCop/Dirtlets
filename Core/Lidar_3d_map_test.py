
import argparse
import asyncio
import math
import multiprocessing as mp
import queue
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

try:
    import open3d as o3d
except Exception:
    o3d = None

from rplidarc1 import RPLidar


BAUD_RATE = 460800
WINDOW_NAME = "RPLIDAR C1 -> 3D Map"
CANVAS_SIZE = 720
MAX_DISTANCE_MM = 8000
MARGIN = 55

VOXEL_SIZE_M = 0.03
MAP_HALF_SIZE_M = 6.0
MAP_HEIGHT_M = 3.5
MAX_X_VOXELS = int((MAP_HALF_SIZE_M * 2.0) / VOXEL_SIZE_M)
MAX_Y_VOXELS = int((MAP_HALF_SIZE_M * 2.0) / VOXEL_SIZE_M)
MAX_Z_VOXELS = int(MAP_HEIGHT_M / VOXEL_SIZE_M)

VIEWER_PUSH_PERIOD_S = 0.10
VIEWER_CLEAN_PERIOD_S = 0.8



# AI coded SERVO Control Re-Write for clarity and maybe seperate from original project


@dataclass
class ServoMount:
    """Describes how the LiDAR is attached to the servo.

    axis         : 'x' or 'y' — the world axis the servo rotates about.
                   'y' means the servo shaft runs left-right across the front
                   of the LiDAR, which is what you want for scanning a room.
    offset_m     : (ox, oy, oz) — vector from the servo PIVOT to the LiDAR
                   ORIGIN, expressed in the servo body frame (i.e. at
                   pitch = 0). Measure this once with a ruler.
    sensor_height_m : height of the LiDAR origin above the floor when pitch=0.
    sign         : +1 or -1 to flip positive pitch direction.
    """
    axis: str = "y"
    offset_m: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    sensor_height_m: float = 0.0
    sign: float = 1.0


def lidar_point_to_world(distance_mm: float, angle_deg: float,
                         pitch_deg: float, mount: ServoMount
                         ) -> Tuple[float, float, float]:
    """Transform a 2D LiDAR sample into a floor-referenced world frame."""
    r = distance_mm / 1000.0
    th = math.radians(angle_deg)
    p = math.radians(pitch_deg * mount.sign)

    # 1. Point in LiDAR body frame.
    bx, by, bz = r * math.cos(th), r * math.sin(th), 0.0

    # 2. Add lever arm: vector from pivot to LiDAR origin, then to the point.
    ox, oy, oz = mount.offset_m
    lx, ly, lz = ox + bx, oy + by, oz + bz

    # 3. Rotate the whole thing about the chosen world axis.
    if mount.axis == "x":
        wx = lx
        wy = ly * math.cos(p) - lz * math.sin(p)
        wz = ly * math.sin(p) + lz * math.cos(p)
    elif mount.axis == "y":
        wx = lx * math.cos(p) + lz * math.sin(p)
        wy = ly
        wz = -lx * math.sin(p) + lz * math.cos(p)
    else:  # 'z' — pan, kept for completeness
        wx = lx * math.cos(p) - ly * math.sin(p)
        wy = lx * math.sin(p) + ly * math.cos(p)
        wz = lz

    # 4. Lift into the floor-referenced frame.
    return wx, wy, wz + mount.sensor_height_m


# Small Servo future proof for the next steps

class ServoBase:
    def set_angle(self, deg: float) -> None: raise NotImplementedError
    def get_angle(self) -> float: return 0.0
    def close(self) -> None: pass


class OpenLoopServo(ServoBase):
    """Software first-order-lag model. Cheap servos only. Never accurate
    enough for metric work, but usable if you dwell long enough."""
    def __init__(self, min_deg, max_deg, lag_s=0.20):
        self.min_deg = float(min_deg); self.max_deg = float(max_deg)
        self.lag_s = float(lag_s)
        self._target = 0.0; self._actual = 0.0
        self._t_last = time.monotonic(); self._lock = threading.Lock()

    def set_angle(self, deg):
        deg = float(np.clip(deg, self.min_deg, self.max_deg))
        with self._lock: self._target = deg

    def get_angle(self):
        with self._lock:
            now = time.monotonic(); dt = now - self._t_last; self._t_last = now
            a = 1.0 - math.exp(-dt / max(self.lag_s, 1e-3))
            self._actual += a * (self._target - self._actual)
            return self._actual


class SerialServo(ServoBase):
    """MCU with a real servo + position feedback (encoder or pot).
    Protocol: host -> board 'P<deg>\\n'; board -> host 'A<deg>\\n'.
    Echo the MEASURED angle if you have one — that's what makes the map sharp."""
    def __init__(self, port, baud=115200, timeout=0.1):
        import serial
        self.ser = serial.Serial(port, baud, timeout=timeout)
        self._lock = threading.Lock(); self._last = 0.0
        self._stop = threading.Event()
        threading.Thread(target=self._read_loop, daemon=True).start()

    def _read_loop(self):
        buf = b""
        while not self._stop.is_set():
            try: chunk = self.ser.read(64)
            except Exception: time.sleep(0.05); continue
            if not chunk: continue
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if line[:1] == b"A":
                    try:
                        with self._lock: self._last = float(line[1:])
                    except ValueError: pass

    def set_angle(self, deg):
        with self._lock: self.ser.write(f"P{deg:.2f}\n".encode())

    def get_angle(self):
        with self._lock: return self._last

    def close(self):
        self._stop.set()
        try: self.ser.close()
        except Exception: pass


class ServoSweeper:
    """Step-and-shoot sweep. Publishes pitch and an in_position flag so the
    main loop can discard points acquired while the servo is still moving."""
    def __init__(self, servo, min_deg, max_deg, step_deg,
                 settle_s, dwell_s, sign=1.0):
        self.servo = servo
        self.min_deg, self.max_deg = float(min_deg), float(max_deg)
        self.step_deg = float(step_deg)
        self.settle_s, self.dwell_s = float(settle_s), float(dwell_s)
        self.sign = float(sign)
        self._lock = threading.Lock()
        self._pitch = 0.0
        self._step_id = 0
        self._in_position = False
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def pitch(self):
        with self._lock: return self._pitch

    @property
    def step_id(self):
        with self._lock: return self._step_id

    @property
    def in_position(self):
        with self._lock: return self._in_position

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread: self._thread.join(timeout=2.0)
        self.servo.close()

    def _run(self):
        steps = list(np.arange(self.min_deg, self.max_deg + 1e-6, self.step_deg))
        if not steps: return
        direction = list(steps)
        while not self._stop.is_set():
            for target in direction:
                if self._stop.is_set(): return
                with self._lock: self._in_position = False
                self.servo.set_angle(target)
                time.sleep(self.settle_s)
                if self._stop.is_set(): return
                measured = self.servo.get_angle() * self.sign
                with self._lock:
                    self._pitch = measured
                    self._step_id += 1
                    self._in_position = True
                time.sleep(self.dwell_s)
                with self._lock: self._in_position = False
            direction = list(reversed(direction)) if direction is steps else list(steps)

def find_port() -> Optional[str]:
    try:
        from serial.tools import list_ports
    except ImportError:
        return None
    for port in list_ports.comports():
        d = f"{port.device} {port.description or ''}".lower()
        if any(n in d for n in ("usb", "serial", "lidar", "cp210", "ch340")):
            return port.device
    return None


class LidarReader:
    def __init__(self, port):
        self.port = port
        self.points: "queue.Queue[Tuple[str, object]]" = queue.Queue()
        self.stop_requested = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_requested.set()
        if self.thread: self.thread.join(timeout=2.0)

    def _run(self):
        lidar = None
        try:
            lidar = RPLidar(self.port, BAUD_RATE)
            self.points.put(("status", f"Connected to {self.port}."))
            asyncio.run(self._scan(lidar))
        except Exception as e:
            self.points.put(("error", f"Lidar error: {e}"))
        finally:
            if lidar:
                try: lidar.reset()
                except Exception: pass
                try: lidar.shutdown()
                except Exception: pass
            self.points.put(("stopped", "Scan stopped."))

    async def _scan(self, lidar):
        scan_task = asyncio.create_task(lidar.simple_scan())
        try:
            while not self.stop_requested.is_set():
                try:
                    pt = await asyncio.wait_for(lidar.output_queue.get(), timeout=0.25)
                except asyncio.TimeoutError:
                    continue
                if isinstance(pt, dict):
                    self.points.put(("point", pt))
        finally:
            lidar.stop_event.set()
            await asyncio.gather(scan_task, return_exceptions=True)

def _add_point(sums, counts, x, y, z):
    ix = int(round(x / VOXEL_SIZE_M))
    iy = int(round(y / VOXEL_SIZE_M))
    iz = int(round(z / VOXEL_SIZE_M))
    if abs(ix) > MAX_X_VOXELS // 2: return False
    if abs(iy) > MAX_Y_VOXELS // 2: return False
    if iz < 0 or iz > MAX_Z_VOXELS: return False
    key = (ix, iy, iz)
    s = sums.get(key)
    if s is None:
        sums[key] = np.array([x, y, z], dtype=np.float64)
        counts[key] = 1
        return True
    s[0] += x; s[1] += y; s[2] += z
    counts[key] += 1
    return True


def _voxel_points(sums, counts):
    if not sums: return np.empty((0, 3), dtype=np.float64)
    out = np.empty((len(sums), 3), dtype=np.float64)
    for i, (k, s) in enumerate(sums.items()):
        out[i] = s / counts[k]
    return out

# Simple 2d vs

def draw_scan(scan_points, status, pitch_deg, in_pos, error=None):
    img = np.full((CANVAS_SIZE, CANVAS_SIZE, 3), 255, dtype=np.uint8)
    c = CANVAS_SIZE // 2; rad = c - MARGIN
    for f in (0.25, 0.5, 0.75, 1.0):
        cv2.circle(img, (c, c), int(rad * f), (215, 225, 228), 1)
    cv2.line(img, (MARGIN, c), (CANVAS_SIZE - MARGIN, c), (225, 230, 232), 1)
    cv2.line(img, (c, MARGIN), (c, CANVAS_SIZE - MARGIN), (225, 230, 232), 1)
    for angle, dist in scan_points.items():
        s = min(dist / MAX_DISTANCE_MM, 1.0) * rad
        r = math.radians(angle - 90)
        cv2.circle(img, (int(c + s * math.cos(r)), int(c + s * math.sin(r))),
                   2, (23, 107, 120), -1)
    cv2.putText(img, f"{status} | pts {len(scan_points)}",
                (15, CANVAS_SIZE - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (31, 45, 51), 1)
    tag = "HOLDING" if in_pos else "settling"
    cv2.putText(img, f"pitch {pitch_deg:+6.2f} deg  [{tag}]",
                (15, CANVAS_SIZE - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (31, 45, 51), 1)
    if error:
        cv2.putText(img, error[:80], (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 180), 1)
    cv2.putText(img, "q quit   c clear   v toggle 3D",
                (15, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 80, 80), 1)
    return img


def _grid(size=12.0, step=1.0, z=0.0):
    half = size / 2.0; n = int(size / step); segs = []
    for i in range(-n, n + 1):
        v = i * step
        segs.append([[-half, v, z], [half, v, z]])
        segs.append([[v, -half, z], [v, half, z]])
    pts = np.asarray(segs, dtype=np.float64).reshape(-1, 3)
    lines = np.asarray([[2 * i, 2 * i + 1] for i in range(len(segs))], dtype=np.int32)
    ls = o3d.geometry.LineSet()
    ls.points = o3d.utility.Vector3dVector(pts)
    ls.lines = o3d.utility.Vector2iVector(lines)
    ls.colors = o3d.utility.Vector3dVector(
        np.tile(np.array([[0.18, 0.20, 0.26]]), (len(segs), 1)))
    return ls


def _color_z(pts):
    z = pts[:, 2]; span = float(z.max() - z.min())
    t = (z - z.min()) / span if span > 1e-6 else np.zeros_like(z)
    r = np.clip(1.5 * t - 0.25, 0, 1)
    g = np.clip(1.5 - np.abs(3.0 * t - 1.5) * 1.2, 0, 1)
    b = np.clip(1.25 - 1.75 * t, 0, 1)
    return np.stack([r, g, b], axis=1)


def _clean(pts, cfg):
    if pts.shape[0] < 10: return pts
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts)
    if cfg["voxel_size"] > 0:
        pcd = pcd.voxel_down_sample(cfg["voxel_size"])
    if cfg["sor_k"] > 0 and len(pcd.points) > cfg["sor_k"]:
        pcd, _ = pcd.remove_statistical_outlier(cfg["sor_k"], cfg["sor_std"])
    if cfg["ror_n"] > 0 and len(pcd.points) > cfg["ror_n"]:
        pcd, _ = pcd.remove_radius_outlier(cfg["ror_n"], cfg["ror_r"])
    return np.asarray(pcd.points)


def _viewer_proc(q, stop_evt, cfg):
    if o3d is None: return
    try:
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name="3D LiDAR Map", width=1280, height=820)
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.zeros((1, 3)))
        pcd.colors = o3d.utility.Vector3dVector(np.zeros((1, 3)))
        vis.add_geometry(pcd)
        vis.add_geometry(o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5))
        vis.add_geometry(_grid(12.0, 1.0, 0.0))
        opt = vis.get_render_option()
        opt.point_size = cfg["point_size"]
        opt.background_color = np.array([0.04, 0.04, 0.07])
        view = vis.get_view_control()
        view.set_lookat([0.0, 0.0, 0.5])
        view.set_up([0.0, 0.0, 1.0])
        view.set_front([0.7, -1.0, -0.4])
        view.set_zoom(0.5)

        last = None; last_clean = 0.0
        while not stop_evt.is_set():
            newest = None
            while True:
                try: newest = q.get_nowait()
                except Exception: break
            if newest is not None: last = newest

            now = time.monotonic()
            if last is not None and last.shape[0] > 0 and \
                    (now - last_clean) > cfg["clean_period"]:
                c = _clean(last, cfg)
                if c.shape[0] > 0:
                    pcd.points = o3d.utility.Vector3dVector(c)
                    pcd.colors = o3d.utility.Vector3dVector(_color_z(c))
                    vis.update_geometry(pcd)
                last_clean = now
            if not vis.poll_events(): break
            vis.update_renderer()
            time.sleep(0.03)
        vis.destroy_window()
    except Exception as e:
        print(f"[viewer] {e}")


class Viewer:
    def __init__(self):
        self._ctx = mp.get_context()
        self._q = self._stop = self._proc = None

    @property
    def running(self):
        return self._proc is not None and self._proc.is_alive()

    def start(self, cfg):
        if o3d is None:
            print("Open3D not installed."); return False
        if self.running: return True
        self._q = self._ctx.Queue(maxsize=2)
        self._stop = self._ctx.Event()
        self._proc = self._ctx.Process(target=_viewer_proc,
                                       args=(self._q, self._stop, cfg), daemon=True)
        self._proc.start(); return True

    def update(self, pts):
        if not self.running: return
        try: self._q.get_nowait()
        except Exception: pass
        try: self._q.put_nowait(pts)
        except Exception: pass

    def stop(self):
        if self._stop: self._stop.set()
        if self._proc:
            self._proc.join(timeout=2.0)
            if self._proc.is_alive(): self._proc.terminate()
        self._q = self._stop = self._proc = None


def synth_scan(_id, _pitch):
    pts = {}
    for a in range(0, 360):
        th = math.radians(a)
        d = 2.0 + 0.5 * math.sin(3 * th) + 0.3 * math.cos(7 * th)
        pts[a] = max(0.4, min(d, 3.5)) * 1000.0
    return pts


def main():
    ap = argparse.ArgumentParser(description="2D LiDAR + servo -> floor-referenced 3D map")

    ap.add_argument("--port", type=str, default=None)
    ap.add_argument("--simulate", action="store_true")

    ap.add_argument("--servo", choices=["openloop", "serial", "none"], default="none")
    ap.add_argument("--servo-port", type=str, default=None)
    ap.add_argument("--servo-baud", type=int, default=115200)
    ap.add_argument("--servo-lag", type=float, default=0.20)

    ap.add_argument("--sweep-min", type=float, default=-40.0)
    ap.add_argument("--sweep-max", type=float, default=40.0)
    ap.add_argument("--sweep-step", type=float, default=1.0)
    ap.add_argument("--settle", type=float, default=0.35)
    ap.add_argument("--dwell", type=float, default=0.70)
    ap.add_argument("--pitch-sign", type=float, default=1.0)

    ap.add_argument("--tilt", type=float, default=25.0,
                    help="Fixed pitch when --servo none")

    # --- Mount geometry ---
    ap.add_argument("--axis", choices=["x", "y"], default="y",
                    help="Servo rotation axis. 'y' is correct for room scanning.")
    ap.add_argument("--offset", type=float, nargs=3, default=[0.0, 0.0, 0.0],
                    metavar=("OX", "OY", "OZ"),
                    help="Vector from servo pivot to LiDAR origin, metres.")
    ap.add_argument("--sensor-height", type=float, default=1.0,
                    help="Height of LiDAR origin above the floor, metres.")

    ap.add_argument("--no-3d", action="store_true")
    ap.add_argument("--point-size", type=float, default=3.0)
    ap.add_argument("--sor-k", type=int, default=20)
    ap.add_argument("--sor-std", type=float, default=2.0)
    ap.add_argument("--ror-n", type=int, default=4)
    ap.add_argument("--ror-r", type=float, default=0.10)

    ap.add_argument("--record", type=str, default=None,
                    help="Save final cloud to this .ply / .pcd on exit")
    ap.add_argument("--mesh", type=str, default=None,
                    help="Also write a Poisson mesh on exit")
    args = ap.parse_args()

    mount = ServoMount(axis=args.axis,
                       offset_m=tuple(args.offset),
                       sensor_height_m=args.sensor_height,
                       sign=args.pitch_sign)

    # --- Sweeper ---
    sweeper = None
    static_pitch = args.tilt
    if args.servo == "openloop":
        servo = OpenLoopServo(args.sweep_min, args.sweep_max, args.servo_lag)
        sweeper = ServoSweeper(servo, args.sweep_min, args.sweep_max,
                               args.sweep_step, args.settle, args.dwell,
                               args.pitch_sign)
        sweeper.start()
        print(f"Open-loop sweep {args.sweep_min}..{args.sweep_max} deg, "
              f"step {args.sweep_step}, settle {args.settle}s, dwell {args.dwell}s")
    elif args.servo == "serial":
        if not args.servo_port:
            print("--servo serial needs --servo-port"); return 1
        servo = SerialServo(args.servo_port, args.servo_baud)
        sweeper = ServoSweeper(servo, args.sweep_min, args.sweep_max,
                               args.sweep_step, args.settle, args.dwell,
                               args.pitch_sign)
        sweeper.start()
        print(f"Serial servo on {args.servo_port} @ {args.servo_baud}")

    # --- LiDAR ---
    port = args.port or find_port()
    if not args.simulate and not port:
        print("No serial port. Use --simulate or pass --port.")
        if sweeper: sweeper.stop()
        return 1
    reader = None
    if not args.simulate:
        reader = LidarReader(port); reader.start()

    # --- Viewer ---
    viewer_cfg = dict(voxel_size=VOXEL_SIZE_M, sor_k=args.sor_k,
                      sor_std=args.sor_std, ror_n=args.ror_n, ror_r=args.ror_r,
                      clean_period=VIEWER_CLEAN_PERIOD_S, point_size=args.point_size)
    viewer = Viewer()
    if not args.no_3d and not viewer.start(viewer_cfg):
        print("Continuing without 3D viewer.")

    # --- State ---
    scan_points: Dict[int, float] = {}
    vox_sums: Dict[Tuple[int, int, int], np.ndarray] = {}
    vox_counts: Dict[Tuple[int, int, int], int] = {}
    status = "Connecting..." if not args.simulate else "Synthetic mode"
    error = None
    sim_id = 0
    last_push = 0.0
    dirty = True

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    try:
        while True:
            pitch = sweeper.pitch if sweeper else static_pitch
            in_pos = sweeper.in_position if sweeper else True

            if args.simulate:
                scan_points = synth_scan(sim_id, pitch); sim_id += 1
                for a, d in scan_points.items():
                    if d > 0 and in_pos:
                        x, y, z = lidar_point_to_world(d, a, pitch, mount)
                        if _add_point(vox_sums, vox_counts, x, y, z):
                            dirty = True
                status = "Synthetic mode"
            else:
                while True:
                    try: kind, val = reader.points.get_nowait()
                    except queue.Empty: break

                    if kind == "point" and isinstance(val, dict):
                        d = val.get("d_mm"); a = val.get("a_deg")
                        try: d = float(d); a = float(a)
                        except (TypeError, ValueError): continue
                        if d <= 0: continue

                        scan_points[int(round(a)) % 360] = d

                        # *** Gate: only accumulate while the servo is holding. ***
                        if not in_pos:
                            continue
                        x, y, z = lidar_point_to_world(d, a, pitch, mount)
                        if _add_point(vox_sums, vox_counts, x, y, z):
                            dirty = True
                    elif kind == "error":
                        error = str(val); status = str(val)
                    elif kind == "status":
                        status = str(val)
                    elif kind == "stopped":
                        status = str(val)

            now = time.monotonic()
            if viewer.running and dirty and (now - last_push) >= VIEWER_PUSH_PERIOD_S:
                viewer.update(_voxel_points(vox_sums, vox_counts))
                last_push = now; dirty = False

            cv2.imshow(WINDOW_NAME, draw_scan(scan_points, status, pitch, in_pos, error))
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"): break
            if key == ord("c"):
                vox_sums.clear(); vox_counts.clear(); scan_points.clear()
                dirty = True
                if viewer.running: viewer.update(np.empty((0, 3)))
            if key == ord("v"):
                if viewer.running: viewer.stop(); print("3D viewer closed.")
                elif viewer.start(viewer_cfg): dirty = True; print("3D viewer opened.")
    finally:
        viewer.stop()
        if sweeper: sweeper.stop()
        if reader: reader.stop()
        cv2.destroyAllWindows()

        pts = _voxel_points(vox_sums, vox_counts)
        if args.record and pts.shape[0] > 0 and o3d is not None:
            print(f"Cleaning {pts.shape[0]} points before export...")
            cleaned = _clean(pts, viewer_cfg)
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(cleaned)
            pcd.colors = o3d.utility.Vector3dVector(_color_z(cleaned))
            o3d.io.write_point_cloud(args.record, pcd)
            print(f"Wrote {cleaned.shape[0]} points to {args.record}")

            if args.mesh:
                pcd.estimate_normals(search_param=o3d.geometry
                                     .KDTreeSearchParamHybrid(radius=0.2, max_nn=30))
                pcd.orient_normals_consistent_tangent_plane(k=30)
                mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                    pcd, depth=9, width=0, scale=1.1, linear_fit=False)
                mesh.compute_vertex_normals()
                o3d.io.write_triangle_mesh(args.mesh, mesh)
                print(f"Wrote mesh to {args.mesh}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())