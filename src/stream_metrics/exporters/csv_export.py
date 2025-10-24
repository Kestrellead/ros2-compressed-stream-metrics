from __future__ import annotations
import csv
def write(summary: dict, path: str = "metrics.csv") -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(summary.keys()); w.writerow(summary.values())
