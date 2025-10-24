#!/usr/bin/env python3
import csv, threading, argparse, time, random
from stream_metrics.metrics import StreamStats
from stream_metrics.transports.memory_bus import MemoryBus, Packet
from stream_metrics.codec import make_encoder
from stream_metrics.generator import synthetic_rgb, synthetic_tof, now_ns

def run(kind, codec, hz, seconds, quality, drop_pct):
    bus = MemoryBus(); stats = StreamStats()
    enc = make_encoder(kind, codec, quality=quality)
    def prod():
        period = 1.0 / hz
        t0 = time.time(); idx = 0
        while time.time() - t0 < seconds:
            img = synthetic_rgb(idx=idx) if kind=="rgb" else synthetic_tof(idx=idx)
            if drop_pct <= 0 or random.random() >= (drop_pct/100.0):
                bb = enc(img); ts = now_ns()
                bus.publish(Packet(ts_ns=ts, payload=bb))
                stats.record_tx(len(bb))
            idx += 1
            next_t = t0 + idx*period
            sl = next_t - time.time()
            if sl > 0: time.sleep(sl)
    def cons():
        t0 = time.time()
        while time.time() - t0 < seconds:
            pkt = bus.subscribe(timeout=0.2)
            if not pkt: continue
            now = time.time_ns()
            stats.record_rx((now - pkt.ts_ns)/1e6, now_ms=now/1e6)
    tp = threading.Thread(target=prod, daemon=True)
    tc = threading.Thread(target=cons, daemon=True)
    tp.start(); tc.start(); tp.join(); tc.join()
    out = stats.summary()
    out.update({"kind":kind,"codec":codec,"hz":hz,"seconds":seconds,"quality":quality,"drop_pct":drop_pct})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=1.0)
    ap.add_argument("--hz", default="10,30")
    ap.add_argument("--kinds", default="rgb,tof")
    ap.add_argument("--codecs-rgb", default="jpeg,png")
    ap.add_argument("--codecs-tof", default="png16")
    ap.add_argument("--quality", type=int, default=80)
    ap.add_argument("--drop-pct", type=float, default=0.0)
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
                cases.append(run(kind, codec, hz, args.seconds, args.quality, args.drop_pct))

    fields = ["kind","codec","hz","seconds","quality","drop_pct",
              "tx","rx","loss_pct","bytes_tx","mb_tx","fps",
              "lat_ms_p50","lat_ms_p95","lat_ms_mean"]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(cases)
    print(f"Wrote {args.out} with {len(cases)} rows.")
if __name__ == "__main__":
    main()
