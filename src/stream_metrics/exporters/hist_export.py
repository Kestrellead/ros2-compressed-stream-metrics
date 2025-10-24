from __future__ import annotations
import csv

def write_histogram(hist: dict[float, int], path: str = "histogram.csv") -> None:
    """Write latency histogram to CSV."""
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["latency_ms", "count"])
        for latency_ms, count in sorted(hist.items()):
            w.writerow([latency_ms, count])

def write_prometheus(hist: dict[float, int], path: str = "histogram.prom") -> None:
    """Write latency histogram to Prometheus exposition format."""
    total = sum(hist.values())
    cumulative = 0
    with open(path, "w") as f:
        for latency_ms, count in sorted(hist.items()):
            cumulative += count
            f.write(f'stream_latency_ms_bucket{{le="{latency_ms}"}} {cumulative}\n')
        f.write(f"stream_latency_ms_bucket{{le=\"+Inf\"}} {total}\n")
        f.write(f"stream_latency_ms_count {total}\n")
