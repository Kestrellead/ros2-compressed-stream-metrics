from __future__ import annotations
import cv2
import numpy as np

def encode_rgb_jpeg(img: np.ndarray, quality: int = 80) -> bytes:
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    return buf.tobytes()

def encode_rgb_png(img: np.ndarray, level: int = 3) -> bytes:
    ok, buf = cv2.imencode(".png", img, [int(cv2.IMWRITE_PNG_COMPRESSION), int(level)])
    if not ok:
        raise RuntimeError("PNG encode failed")
    return buf.tobytes()

def encode_depth_png16(depth: np.ndarray, level: int = 3) -> bytes:
    if depth.dtype != np.uint16:
        depth = depth.astype(np.uint16)
    ok, buf = cv2.imencode(".png", depth, [int(cv2.IMWRITE_PNG_COMPRESSION), int(level)])
    if not ok:
        raise RuntimeError("PNG16 encode failed")
    return buf.tobytes()
