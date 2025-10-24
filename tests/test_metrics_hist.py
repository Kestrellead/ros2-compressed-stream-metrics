from stream_metrics.metrics import StreamStats
def test_hist_and_fps():
    s = StreamStats()
    # simulate rx over 1s
    for i in range(10):
        s.record_tx(100)
        s.record_rx(5.0, now_ms=1000 + i*100)
    h = s.histogram()
    assert sum(v for k,v in h.items() if k!="over") + h["over"] == 10
    assert s.fps() is not None
