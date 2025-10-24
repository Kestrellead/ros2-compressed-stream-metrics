from __future__ import annotations
from .memory_bus import MemoryBus
from .impair import ImpairedBus
try:
    from .zmq_bus import ZmqBus
except Exception:  # optional dep
    ZmqBus = None

def make_bus(kind: str, endpoint: str, net_latency_ms: float, net_jitter_ms: float, drop_pct_rx: float):
    if kind == "memory":
        base = MemoryBus()
    elif kind == "zmq":
        if ZmqBus is None:
            raise RuntimeError("pyzmq not installed")
        base = ZmqBus(endpoint=endpoint)
    else:
        raise ValueError(f"unknown bus kind: {kind}")
    use_imp = (net_latency_ms > 0.0) or (net_jitter_ms > 0.0) or (drop_pct_rx > 0.0)
    return ImpairedBus(base, net_latency_ms, net_jitter_ms, drop_pct_rx) if use_imp else base
