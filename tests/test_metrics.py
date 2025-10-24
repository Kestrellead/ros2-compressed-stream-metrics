from stream_metrics.metrics import StreamStats

def test_stats_basic():
    s = StreamStats()
    for _ in range(10):
        s.record_tx(1000)
    for _ in range(8):
        s.record_rx(5.0)
    out = s.summary()
    assert out["tx"] == 10
    assert out["rx"] == 8
    assert out["loss_pct"] == 20.0
    assert out["lat_ms_mean"] == 5.0
