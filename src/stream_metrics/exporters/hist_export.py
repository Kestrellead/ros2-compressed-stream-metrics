from __future__ import annotations
import csv
from typing import Dict, Union

Num = Union[int, float]

def _split(hist: Dict[Union[str, Num], int]):
    h = dict(hist)
    over = h.pop("over", 0)
    # keep only numeric keys, sort ascending
    items = sorted([(float(k), int(v)) for k, v in h.items()], key=lambda x: x[0])
    return items, int(over)

def write_histogram(hist: dict[Union[str, Num], int], path: str = "histogram.csv") -> None:
    items, over = _split(hist)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["latency_ms", "count"])
        for ms, count in items:
            w.writerow([ms, count])
        w.writerow(["+Inf", over])

def write_prometheus(hist: dict[Union[str, Num], int], path: str = "histogram.prom") -> None:
    items, over = _split(hist)
    total = sum(c for _, c in items) + over
    cumulative = 0
    with open(path, "w") as f:
        for ms, count in items:
            cumulative += count
            f.write(f'stream_latency_ms_bucket{{le="{ms}"}} {cumulative}\n')
        f.write(f'stream_latency_ms_bucket{{le="+Inf"}} {total}\n')
        f.write(f"stream_latency_ms_count {total}\n")
