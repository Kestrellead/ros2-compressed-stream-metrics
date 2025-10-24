from __future__ import annotations
import argparse, time, threading, random
from rich.console import Console
from rich.table import Table
from rich.live import Live
from .generator import synthetic_rgb, synthetic_tof, now_ns
from .codec import make_encoder
from .metrics import StreamStats
from .transports.bus_factory import make_bus
from .transports.memory_bus import Packet
from .exporters.csv_export import write as csv_write
from .exporters.prom_export import format_prometheus
from .exporters.hist_export import write_histogram, write_prometheus as write_hist_prom

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
    ap = argparse.ArgumentParser(description="Compressed streaming with metrics.")
    ap.add_argument("--bus", choices=["memory","zmq"], default="memory")
    ap.add_argument("--endpoint", default="tcp://127.0.0.1:5556")
    ap.add_argument("--kind", choices=["rgb","tof"], default="rgb")
    ap.add_argument("--codec", choices=["jpeg","png","png16"], default="jpeg")
    ap.add_argument("--hz", type=float, default=30.0)
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--quality", type=int, default=80)
    ap.add_argument("--drop-pct", type=float, default=0.0)
    ap.add_argument("--net-latency-ms", type=float, default=0.0)
    ap.add_argument("--net-jitter-ms", type=float, default=0.0)
    ap.add_argument("--drop-pct-rx", type=float, default=0.0)
    ap.add_argument("--csv", type=str, default="")
    ap.add_argument("--prom", type=str, default="")
    ap.add_argument("--hist-csv", type=str, default="")
    ap.add_argument("--hist-prom", type=str, default="")
    ap.add_argument("--visualize", action="store_true")
    args = ap.parse_args()

    bus = make_bus(args.bus, args.endpoint, args.net_latency_ms, args.net_jitter_ms, args.drop_pct_rx)
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
    if args.hist_csv or args.hist_prom:
        hist = stats.histogram()
        if args.hist_csv:
            write_histogram(hist, args.hist_csv); console.print(f"[dim]wrote {args.hist_csv}[/dim]")
        if args.hist_prom:
            write_hist_prom(hist, args.hist_prom); console.print(f"[dim]wrote {args.hist_prom}[/dim]")

if __name__ == "__main__":
    main()
