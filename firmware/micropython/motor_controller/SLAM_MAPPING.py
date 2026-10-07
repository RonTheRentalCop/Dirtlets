# How will I go about creating a 3d map with a 2d lidar sensor?

from lidar import RPLidar
import time
import argparse
import asyncio
import math
import multiprocessing as mp
import queue
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import cv2
import numpy as np
import pynamixel
from smart_servo_library import SerialBus
try:
    import open3d as o3d
except ImportError:
    o3d = None

BAUD_RATE = 460800
WINDOW_NAME = "3d SLAM MAP"
CANVAS_SIZE = 720
MAX_DISTANCE = 120000  # Maximum distance the lidar can measure in millimeters
MARGIN = 50

VOXEL_SIZE = 0.05
MAP_HALF_SIZE_M = 6.0
MAP_HEIGHT_M = 3.5
MAX_X_VOXELS = int((MAP_HALF_SIZE_M * 2.0) / VOXEL_SIZE_M)
MAX_Y_VOXELS = int((MAP_HALF_SIZE_M * 2.0) / VOXEL_SIZE_M)
MAX_Z_VOXELS = int(MAP_HEIGHT_M / VOXEL_SIZE_M)

VIEWER_PUSH_PERIOD_S = 0.10
VIEWER_CLEAN_PERIOD_S = 0.8

X

# I need to take my smart servo and mount the 2d lidar sensor onto it so that it can rotate and capture 3d data.



# I then can turn the sensor up and down to capture the enviornemnt. 
# By combining the 2d scans from different angles, I can reconstruct a 3d map of the surroundings.

# After that I ned to take the telematry data and the servos smart feedback positions to then calculate the exact position of the data provided to the bot
# Finally I can put it together to make a map




# THINGS TO NOTE

# - That I can run multiple instences of these programs to support multipl drones.
# - I need to account for latency in the sensor and servo feedback to ensure accurate mapping.
# - I need to have this done by some deadline because I need to collect data. 