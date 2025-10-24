from __future__ import annotations
import argparse, time, threading, random
from rich.console import Console
from rich.table import Table
from rich.live import Live
from .generator import synthetic_rgb, synthetic_tof, now_ns
from .codec import make_encoder
from .metrics import StreamStats
from .transports.memory_bus import MemoryBus, Packet
from .transports.impair import ImpairedBus
from .exporters.csv_export import write as csv_write
from .exporters.prom_export import format_prometheus

console = Console()

def producer(bus, kind: str, codec: str, hz: float,
             stats: StreamStats, duration_s: float, quality: int, drop_pct: float) -> None:
    enc = make_encoder(kind, codec, quality=quality)
    period = 1.0 / hz
    idx = 0
    t0 = time.time()
    while time.time() - t0 < duration_s:
        img = synthetic_rgb(idx=idx) if kind == "rgb" else synthetic_tof(idx=idx)
        if drop_pct <= 0 or random.random() >= (drop_pct/100.0):
            bb = enc(img)
            ts = now_ns()
            bus.publish(Packet(ts_ns=ts, payload=bb))
            stats.record_tx(len(bb))
        idx += 1
        next_t = t0 + idx * period
        sl = next_t - time.time()
        if sl > 0:
            time.sleep(sl)

def consumer(bus, stats: StreamStats, duration_s: float) -> None:
    t0 = time.time()
    while time.time() - t0 < duration_s:
        pkt = bus.subscribe(timeout=0.2)
        if pkt is None:
            continue
        now_ns = time.time_ns()
        lat_ms = (now_ns - pkt.ts_ns) / 1e6
        stats.record_rx(lat_ms, now_ms=now_ns/1e6)

def render_table(stats: StreamStats) -> Table:
    t = Table(title="Stream Live")
    t.add_column("Metric"); t.add_column("Value")
    s = stats.summary()
    for k in ["tx","rx","loss_pct","mb_tx","fps","lat_ms_p50","lat_ms_p95","lat_ms_mean"]:
        t.add_row(k, str(s.get(k)))
    return t

def main():
    ap = argparse.ArgumentParser(description="Simulated compressed streaming with latency/loss metrics.")
    ap.add_argument("--kind", choices=["rgb","tof"], default="rgb")
    ap.add_argument("--codec", choices=["jpeg","png","png16"], default="jpeg")
    ap.add_argument("--hz", type=float, default=30.0)
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--quality", type=int, default=80, help="Compression quality (10–100)")
    ap.add_argument("--drop-pct", type=float, default=0.0, help="Simulate publish drop percent [0..100]")
    ap.add_argument("--net-latency-ms", type=float, default=0.0, help="Extra one-way latency on receive path")
    ap.add_argument("--net-jitter-ms", type=float, default=0.0, help="Stddev of latency jitter (gaussian)")
    ap.add_argument("--drop-pct-rx", type=float, default=0.0, help="Simulate drop on receive path [0..100]")
    ap.add_argument("--csv", type=str, default="", help="Write summary CSV to this path")
    ap.add_argument("--prom", type=str, default="", help="Write Prometheus textfile to this path")
    ap.add_argument("--visualize", action="store_true", help="Live update table while running")
    args = ap.parse_args()

    base_bus = MemoryBus()
    use_imp = (args.net_latency_ms > 0.0) or (args.net_jitter_ms > 0.0) or (args.drop_pct_rx > 0.0)
    bus = ImpairedBus(base_bus, args.net_latency_ms, args.net_jitter_ms, args.drop_pct_rx) if use_imp else base_bus

    stats = StreamStats()

    th_p = threading.Thread(target=producer, args=(
        bus, args.kind, args.codec, args.hz, stats, args.seconds, args.quality, args.drop_pct
    ), daemon=True)
    th_c = threading.Thread(target=consumer, args=(bus, stats, args.seconds), daemon=True)
    th_p.start(); th_c.start()

    if args.visualize:
        with Live(render_table(stats), refresh_per_second=8, console=console) as live:
            while th_p.is_alive() or th_c.is_alive():
                live.update(render_table(stats))
                time.sleep(0.12)

    th_p.join(); th_c.join()

    summary = stats.summary()
    table = Table(title="Stream Summary")
    for k in ["tx","rx","loss_pct","mb_tx","fps","lat_ms_p50","lat_ms_p95","lat_ms_mean"]:
        table.add_row(k, str(summary[k]))
    console.print(table)

    if args.csv:
        csv_write(summary, args.csv); console.print(f"[dim]wrote {args.csv}[/dim]")
    if args.prom:
        with open(args.prom, "w") as f: f.write(format_prometheus(summary))
        console.print(f"[dim]wrote {args.prom}[/dim]")

if __name__ == "__main__":
    main()
