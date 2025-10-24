#!/usr/bin/env python3
from stream_metrics.cli import producer, consumer
from stream_metrics.metrics import StreamStats
from stream_metrics.transports.memory_bus import MemoryBus
import csv, time, threading, sys

def run(kind="rgb", codec="jpeg", hz=30.0, seconds=10.0, out="metrics.csv"):
    bus = MemoryBus()
    stats = StreamStats()
    th_p = threading.Thread(target=producer, args=(bus, kind, codec, hz, stats, seconds), daemon=True)
    th_c = threading.Thread(target=consumer, args=(bus, stats, seconds), daemon=True)
    th_p.start(); th_c.start(); th_p.join(); th_c.join()
    s = stats.summary()
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(s.keys())
        w.writerow(s.values())
    print(f"Wrote {out}")

if __name__ == "__main__":
    run(*sys.argv[1:])  # optional args ignored for simplicity
