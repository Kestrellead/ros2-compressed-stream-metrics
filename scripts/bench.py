#!/usr/bin/env python3
import csv, threading
from stream_metrics.cli import producer, consumer
from stream_metrics.metrics import StreamStats
from stream_metrics.transports.memory_bus import MemoryBus

def run(kind, codec, hz, seconds=5):
    bus = MemoryBus(); stats = StreamStats()
    tp = threading.Thread(target=producer, args=(bus, kind, codec, hz, stats, seconds), daemon=True)
    tc = threading.Thread(target=consumer, args=(bus, stats, seconds), daemon=True)
    tp.start(); tc.start(); tp.join(); tc.join()
    out = stats.summary(); out.update({"kind": kind, "codec": codec, "hz": hz})
    return out

def main():
    cases = []
    for kind, codec_list in [("rgb", ["jpeg","png"]), ("tof", ["png16"])]:
        for codec in codec_list:
            for hz in [10, 20, 30, 60]:
                cases.append(run(kind, codec, hz))
    with open("bench.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kind","codec","hz","tx","rx","loss_pct","mb_tx","lat_ms_p50","lat_ms_p95","lat_ms_mean"])
        w.writeheader(); w.writerows(cases)
    print("Wrote bench.csv")

if __name__ == "__main__":
    main()
