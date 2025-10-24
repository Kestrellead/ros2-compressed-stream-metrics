#!/usr/bin/env python3
from __future__ import annotations
import argparse, time, random
from stream_metrics.generator import synthetic_rgb, synthetic_tof, now_ns
from stream_metrics.codec import make_encoder
from stream_metrics.transports.zmq_bus import ZmqBus, Packet

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="tcp://127.0.0.1:5556")
    ap.add_argument("--kind", choices=["rgb","tof"], default="rgb")
    ap.add_argument("--codec", choices=["jpeg","png","png16"], default="jpeg")
    ap.add_argument("--hz", type=float, default=30.0)
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--quality", type=int, default=80)
    ap.add_argument("--drop-pct", type=float, default=0.0)
    args = ap.parse_args()

    bus = ZmqBus(endpoint=args.endpoint)
    enc = make_encoder(args.kind, args.codec, quality=args.quality)
    period = 1.0 / args.hz
    t0, idx = time.time(), 0
    while time.time() - t0 < args.seconds:
        img = synthetic_rgb(idx=idx) if args.kind == "rgb" else synthetic_tof(idx=idx)
        if args.drop_pct <= 0 or random.random() >= (args.drop_pct/100.0):
            bb = enc(img)
            bus.publish(Packet(ts_ns=now_ns(), payload=bb))
        idx += 1
        sl = t0 + idx*period - time.time()
        if sl > 0: time.sleep(sl)

if __name__ == "__main__":
    main()
