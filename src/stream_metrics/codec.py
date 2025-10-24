from __future__ import annotations
import cv2
import numpy as np
from typing import Callable, Tuple

EncodeFn = Callable[[np.ndarray], bytes]

def make_encoder(kind: str, codec: str, quality: int = 80) -> EncodeFn:
    if kind == "rgb" and codec == "jpeg":
        q = int(np.clip(quality, 10, 100))
        return lambda img: _encode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), q])
    if kind == "rgb" and codec == "png":
        # map quality (10..100) -> png level (0..9), lower is faster
        level = int(np.clip(round((100 - quality) * 9 / 90), 0, 9))
        return lambda img: _encode(".png", img, [int(cv2.IMWRITE_PNG_COMPRESSION), level])
    if kind == "tof" and codec == "png16":
        level = int(np.clip(round((100 - quality) * 9 / 90), 0, 9))
        return lambda depth: _encode(".png", depth.astype(np.uint16), [int(cv2.IMWRITE_PNG_COMPRESSION), level])
    raise ValueError(f"unsupported kind/codec: {kind}/{codec}")

def _encode(ext: str, arr: np.ndarray, params: list[int]) -> bytes:
    ok, buf = cv2.imencode(ext, arr, params)
    if not ok:
        raise RuntimeError(f"encode failed: {ext}")
    return buf.tobytes()
