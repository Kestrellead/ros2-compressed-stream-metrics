from __future__ import annotations
import numpy as np
import time

def synthetic_rgb(width: int = 640, height: int = 480, idx: int = 0) -> np.ndarray:
    x = np.linspace(0, 255, width, dtype=np.uint8)
    y = np.linspace(0, 255, height, dtype=np.uint8)
    xv, yv = np.meshgrid(x, y)
    base = np.stack([xv, yv, ((xv.astype(int)+yv.astype(int)) % 256).astype(np.uint8)], axis=-1)
    base = np.roll(base, shift=(idx // 2) % width, axis=1)
    return base

def synthetic_tof(width: int = 320, height: int = 240, idx: int = 0) -> np.ndarray:
    xv = np.linspace(0, 6.2831853, width, dtype=np.float32)
    yv = np.linspace(0, 6.2831853, height, dtype=np.float32)
    xx, yy = np.meshgrid(xv, yv)
    depth = 1000 + 300 * np.sin(xx + idx * 0.1) * np.cos(yy * 0.7)
    depth = depth.clip(0, 65535).astype(np.uint16)
    return depth

def now_ns() -> int:
    return time.time_ns()
