from __future__ import annotations
import random, time
from dataclasses import dataclass

@dataclass
class Packet:
    ts_ns: int
    payload: bytes

class ImpairedBus:
    """
    Wraps a bus with publish/subscribe(ts_ns,payload) API and injects latency/jitter/drop on receive.
    """
    def __init__(self, inner, latency_ms: float = 0.0, jitter_ms: float = 0.0, drop_pct_rx: float = 0.0):
        self.inner = inner
        self.latency_ms = max(0.0, float(latency_ms))
        self.jitter_ms = max(0.0, float(jitter_ms))
        self.drop_pct_rx = max(0.0, float(drop_pct_rx))

    def publish(self, pkt: Packet) -> None:
        self.inner.publish(pkt)

    def subscribe(self, timeout: float | None = 1.0):
        pkt = self.inner.subscribe(timeout=timeout)
        if pkt is None:
            return None
        if self.drop_pct_rx > 0.0 and random.random() < (self.drop_pct_rx / 100.0):
            return None
        if self.latency_ms > 0.0 or self.jitter_ms > 0.0:
            # gaussian jitter; clamp to >= 0
            extra = self.latency_ms + (random.gauss(0.0, self.jitter_ms) if self.jitter_ms > 0 else 0.0)
            if extra > 0:
                time.sleep(extra / 1000.0)
        return pkt
