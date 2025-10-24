import numpy as np
from stream_metrics.codec import make_encoder
def test_make_encoder_jpeg_quality_bounds():
    enc = make_encoder("rgb","jpeg", quality=5)   # clamps
    img = np.zeros((10,10,3), dtype=np.uint8)
    out = enc(img)
    assert isinstance(out, (bytes, bytearray))
