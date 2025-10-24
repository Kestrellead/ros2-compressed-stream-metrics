import numpy as np
from stream_metrics.generator import synthetic_rgb, synthetic_tof
def test_rgb_shape():
    img = synthetic_rgb(64, 48, 3)
    assert img.shape == (48, 64, 3)
    assert img.dtype == np.uint8
def test_tof_shape():
    d = synthetic_tof(32, 24, 5)
    assert d.shape == (24, 32)
    assert d.dtype == np.uint16
