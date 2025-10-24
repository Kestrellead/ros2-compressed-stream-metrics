from __future__ import annotations
import argparse, time, threading
from rich.console import Console
from rich.table import Table
from .generator import synthetic_rgb, synthetic_tof, now_ns
from .codec import encode_rgb_jpeg, encode_rgb_png, encode_depth_png16
from .metrics import StreamStats
from .transports.memory_bus import MemoryBus, Packet
from .exporters.csv_export import write as csv_write
from .exporters.prom_export import format_prometheus

console = Console()

def producer(bus: MemoryBus, kind: str, codec: str, hz: float, stats: StreamStats, duration_s: float) -> None:
    enc = {
        ("rgb","jpeg"): lambda img: encode_rgb_jpeg(img, 80),
        ("rgb","png"):  lambda img: encode_rgb_png(img, 3),
        ("tof","png16"):lambda d:   encode_depth_png16(d, 3),
    }[(kind, codec)]
    period = 1.0 / hz
    idx = 0
    t0 = time.time()
    while time.time() - t0 < duration_s:
        img = synthetic_rgb(idx=idx) if kind == "rgb" else synthetic_tof(idx=idx)
        bb = enc(img)
        ts = now_ns()
        bus.publish(Packet(ts_ns=ts, payload=bb))
        stats.record_tx(len(bb))
        idx += 1
        next_t = t0 + idx * period
        sleep_left = next_t - time.time()
        if sleep_left > 0:
            time.sleep(sleep_left)

def consumer(bus: MemoryBus, stats: StreamStats, duration_s: float) -> None:
    t0 = time.time()
    while time.time() - t0 < duration_s:
        pkt = bus.subscribe(timeout=0.2)
        if pkt is None:
            continue
        now = time.time_ns()
        lat_ms = (now - pkt.ts_ns) / 1e6
        stats.record_rx(lat_ms)

def main():
    ap = argparse.ArgumentParser(description="Simulated compressed streaming with latency/loss metrics.")
    ap.add_argument("--kind", choices=["rgb","tof"], default="rgb")
    ap.add_argument("--codec", choices=["jpeg","png","png16"], default="jpeg")
    ap.add_argument("--hz", type=float, default=30.0)
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--csv", type=str, default="", help="Write summary CSV to this path")
    ap.add_argument("--prom", type=str, default="", help="Write Prometheus textfile to this path")
    args = ap.parse_args()

    bus = MemoryBus()
    stats = StreamStats()

    th_p = threading.Thread(target=producer, args=(bus, args.kind, args.codec, args.hz, stats, args.seconds), daemon=True)
    th_c = threading.Thread(target=consumer, args=(bus, stats, args.seconds), daemon=True)

    th_p.start(); th_c.start()
    th_p.join(); th_c.join()

    table = Table(title="Stream Summary")
    summary = stats.summary()
    for k in ["tx","rx","loss_pct","mb_tx","lat_ms_p50","lat_ms_p95","lat_ms_mean"]:
        table.add_row(k, str(summary[k]))
    console.print(table)

    if args.csv:
        csv_write(summary, args.csv)
        console.print(f"[dim]wrote {args.csv}[/dim]")
    if args.prom:
        with open(args.prom, "w") as f:
            f.write(format_prometheus(summary))
        console.print(f"[dim]wrote {args.prom}[/dim]")

if __name__ == "__main__":
    main()
