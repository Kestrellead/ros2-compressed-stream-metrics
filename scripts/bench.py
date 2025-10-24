#!/usr/bin/env python3
import csv, threading, argparse
from stream_metrics.cli import producer, consumer
from stream_metrics.metrics import StreamStats
from stream_metrics.transports.memory_bus import MemoryBus

def run(kind, codec, hz, seconds):
    bus = MemoryBus(); stats = StreamStats()
    tp = threading.Thread(target=producer, args=(bus, kind, codec, hz, stats, seconds), daemon=True)
    tc = threading.Thread(target=consumer, args=(bus, stats, seconds), daemon=True)
    tp.start(); tc.start(); tp.join(); tc.join()
    out = stats.summary()
    out.update({"kind": kind, "codec": codec, "hz": hz, "seconds": seconds})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--hz", default="10,20,30,60")
    ap.add_argument("--kinds", default="rgb,tof")
    ap.add_argument("--codecs-rgb", default="jpeg,png")
    ap.add_argument("--codecs-tof", default="png16")
    ap.add_argument("--out", default="bench.csv")
    args = ap.parse_args()

    hz_list = [float(x) for x in args.hz.split(",") if x]
    kinds = [k.strip() for k in args.kinds.split(",") if k]
    codecs_rgb = [c.strip() for c in args.codecs_rgb.split(",") if c]
    codecs_tof = [c.strip() for c in args.codecs_tof.split(",") if c]

    cases = []
    for kind in kinds:
        codec_list = codecs_rgb if kind == "rgb" else codecs_tof
        for codec in codec_list:
            for hz in hz_list:
                cases.append(run(kind, codec, hz, args.seconds))

    fields = [
        "kind","codec","hz","seconds",
        "tx","rx","loss_pct","bytes_tx","mb_tx",
        "lat_ms_p50","lat_ms_p95","lat_ms_mean"
    ]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(cases)
    print(f"Wrote {args.out} with {len(cases)} rows.")
if __name__ == "__main__":
    main()
