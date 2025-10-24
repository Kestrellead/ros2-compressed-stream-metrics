from __future__ import annotations
from dataclasses import dataclass, field
import statistics, math

@dataclass
class StreamStats:
    count_tx: int = 0
    count_rx: int = 0
    bytes_tx: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    t_first_ms: float | None = None
    t_last_ms: float | None = None

    def record_tx(self, nbytes: int) -> None:
        self.count_tx += 1
        self.bytes_tx += int(nbytes)

    def record_rx(self, latency_ms: float, now_ms: float | None = None) -> None:
        self.count_rx += 1
        self.latencies_ms.append(float(latency_ms))
        if now_ms is not None:
            if self.t_first_ms is None:
                self.t_first_ms = now_ms
            self.t_last_ms = now_ms

    def fps(self) -> float | None:
        if self.t_first_ms is None or self.t_last_ms is None or self.t_last_ms <= self.t_first_ms:
            return None
        dur_s = (self.t_last_ms - self.t_first_ms) / 1_000.0
        return self.count_rx / dur_s if dur_s > 0 else None

    def histogram(self, bins_ms: list[float] = (1,2,4,8,16,33,66,100,200)) -> dict:
        counts = {b: 0 for b in bins_ms}
        over = 0
        for v in self.latencies_ms:
            placed = False
            for b in bins_ms:
                if v <= b:
                    counts[b] += 1
                    placed = True
                    break
            if not placed:
                over += 1
        counts["over"] = over
        return counts

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
            "fps": round(self.fps(), 3) if self.fps() else None,
        }

def quantile(data: list[float], q: float) -> float:
    data = sorted(data)
    if not data:
        return 0.0
    pos = (len(data) - 1) * q
    lower, upper = int(pos), min(int(pos) + 1, len(data) - 1)
    frac = pos - lower
    return data[lower] * (1 - frac) + data[upper] * frac
