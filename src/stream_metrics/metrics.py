from __future__ import annotations
from dataclasses import dataclass, field
import statistics

@dataclass
class StreamStats:
    count_tx: int = 0
    count_rx: int = 0
    bytes_tx: int = 0
    latencies_ms: list[float] = field(default_factory=list)

    def record_tx(self, nbytes: int) -> None:
        self.count_tx += 1
        self.bytes_tx += int(nbytes)

    def record_rx(self, latency_ms: float) -> None:
        self.count_rx += 1
        self.latencies_ms.append(float(latency_ms))

    def summary(self) -> dict:
        loss = 0.0
        if self.count_tx:
            loss = max(0.0, 100.0 * (self.count_tx - self.count_rx) / self.count_tx)
        lat = self.latencies_ms
        return {
            "tx": self.count_tx,
            "rx": self.count_rx,
            "loss_pct": round(loss, 3),
            "bytes_tx": self.bytes_tx,
            "mb_tx": round(self.bytes_tx / (1024 * 1024), 3),
            "lat_ms_p50": round(statistics.median(lat), 3) if lat else None,
            "lat_ms_p95": round(quantile(lat, 0.95), 3) if len(lat) >= 5 else None,
            "lat_ms_mean": round(statistics.fmean(lat), 3) if lat else None,
        }

def quantile(data: list[float], q: float) -> float:
    data = sorted(data)
    if not data:
        return 0.0
    pos = (len(data) - 1) * q
    lower, upper = int(pos), min(int(pos) + 1, len(data) - 1)
    frac = pos - lower
    return data[lower] * (1 - frac) + data[upper] * frac
