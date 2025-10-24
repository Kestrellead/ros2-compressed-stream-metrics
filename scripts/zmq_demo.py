#!/usr/bin/env python3
from __future__ import annotations
import argparse, threading, time
from rich.console import Console
from rich.table import Table
from stream_metrics.generator import synthetic_rgb, synthetic_tof, now_ns
from stream_metrics.codec import encode_rgb_jpeg, encode_rgb_png, encode_depth_png16
from stream_metrics.metrics import StreamStats
from stream_metrics.transports.zmq_bus import ZmqBus, Packet

console = Console()

def producer(bus: ZmqBus, kind: str, codec: str, hz: float, stats: StreamStats, seconds: float):
    enc = {
        ("rgb","jpeg"): lambda img: encode_rgb_jpeg(img, 80),
        ("rgb","png"):  lambda img: encode_rgb_png(img, 3),
        ("tof","png16"):lambda d:   encode_depth_png16(d, 3),
    }[(kind, codec)]
    period = 1.0 / hz
    idx = 0
    t0 = time.time()
    while time.time() - t0 < seconds:
        img = synthetic_rgb(idx=idx) if kind == "rgb" else synthetic_tof(idx=idx)
        payload = enc(img)
        ts = now_ns()
        bus.publish(Packet(ts_ns=ts, payload=payload))
        stats.record_tx(len(payload))
        idx += 1
        next_t = t0 + idx * period
        sleep_left = next_t - time.time()
        if sleep_left > 0:
            time.sleep(sleep_left)

def consumer(bus: ZmqBus, stats: StreamStats, seconds: float):
    t0 = time.time()
    while time.time() - t0 < seconds:
        pkt = bus.subscribe(timeout=0.2)
        if pkt is None:
            continue
        lat_ms = (time.time_ns() - pkt.ts_ns) / 1e6
        stats.record_rx(lat_ms)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["rgb","tof"], default="rgb")
    ap.add_argument("--codec", choices=["jpeg","png","png16"], default="jpeg")
    ap.add_argument("--hz", type=float, default=30.0)
    ap.add_argument("--seconds", type=float, default=5.0)
    args = ap.parse_args()

    bus = ZmqBus()
    stats = StreamStats()

    th_p = threading.Thread(target=producer, args=(bus, args.kind, args.codec, args.hz, stats, args.seconds), daemon=True)
    th_c = threading.Thread(target=consumer, args=(bus, stats, args.seconds), daemon=True)
    th_p.start(); th_c.start(); th_p.join(); th_c.join()

    table = Table(title="ZeroMQ Stream Summary")
    s = stats.summary()
    for k in ["tx","rx","loss_pct","mb_tx","lat_ms_p50","lat_ms_p95","lat_ms_mean"]:
        table.add_row(k, str(s[k]))
    console.print(table)

if __name__ == "__main__":
    main()
