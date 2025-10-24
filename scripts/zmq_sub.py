#!/usr/bin/env python3
from __future__ import annotations
import argparse, time
from rich.table import Table
from rich.console import Console
from stream_metrics.metrics import StreamStats
from stream_metrics.transports.zmq_bus import ZmqBus
from stream_metrics.transports.impair import ImpairedBus

console = Console()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="tcp://127.0.0.1:5556")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--net-latency-ms", type=float, default=0.0)
    ap.add_argument("--net-jitter-ms", type=float, default=0.0)
    ap.add_argument("--drop-pct-rx", type=float, default=0.0)
    args = ap.parse_args()

    base = ZmqBus(endpoint=args.endpoint)
    bus = ImpairedBus(base, args.net_latency_ms, args.net_jitter_ms, args.drop_pct_rx)
    stats = StreamStats()
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        pkt = bus.subscribe(timeout=0.2)
        if not pkt: continue
        now = time.time_ns()
        stats.record_rx((now - pkt.ts_ns)/1e6, now_ms=now/1e6)

    s = stats.summary()
    table = Table(title="ZMQ Subscriber Summary")
    for k in ["rx","loss_pct","fps","lat_ms_p50","lat_ms_p95","lat_ms_mean"]:
        table.add_row(k, str(s.get(k)))
    console.print(table)

if __name__ == "__main__":
    main()
