#!/usr/bin/env python3
from __future__ import annotations
import argparse, threading, time
from rclpy.node import Node
import rclpy
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from builtin_interfaces.msg import Time as RosTime
from sensor_msgs.msg import CompressedImage
from stream_metrics.generator import synthetic_rgb, synthetic_tof, now_ns
from stream_metrics.codec import encode_rgb_jpeg, encode_rgb_png, encode_depth_png16
from stream_metrics.metrics import StreamStats

def to_ros_time_ns(t_ns: int) -> RosTime:
    sec = t_ns // 1_000_000_000
    nsec = t_ns % 1_000_000_000
    return RosTime(sec=sec, nanosec=nsec)

class Pub(Node):
    def __init__(self, kind: str, codec: str, hz: float, seconds: float):
        super().__init__('stream_pub')
        self.kind, self.codec = kind, codec
        self.period = 1.0 / hz
        self.t_end = time.time() + seconds
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.pub = self.create_publisher(CompressedImage, '/stream/compressed', qos)
        self.timer = self.create_timer(self.period, self.tick)
        self.idx = 0
        self.enc = {
            ('rgb','jpeg'): lambda img: encode_rgb_jpeg(img, 80),
            ('rgb','png'):  lambda img: encode_rgb_png(img, 3),
            ('tof','png16'):lambda d:   encode_depth_png16(d, 3),
        }[(kind, codec)]

    def tick(self):
        if time.time() >= self.t_end:
            self.destroy_timer(self.timer)
            return
        img = synthetic_rgb(idx=self.idx) if self.kind == 'rgb' else synthetic_tof(idx=self.idx)
        bb = self.enc(img)
        t_ns = now_ns()
        msg = CompressedImage()
        msg.header.stamp = to_ros_time_ns(t_ns)
        msg.format = self.codec
        msg.data = bb
        self.pub.publish(msg)
        self.idx += 1

class Sub(Node):
    def __init__(self, stats: StreamStats, seconds: float):
        super().__init__('stream_sub')
        self.stats = stats
        self.t_end = time.time() + seconds + 1.0
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.sub = self.create_subscription(
            CompressedImage, '/stream/compressed', self.cb, qos
        )
        self.timer = self.create_timer(0.5, self.check_done)

    def cb(self, msg: CompressedImage):
        t_rx = time.time_ns()
        t_tx = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
        lat_ms = (t_rx - t_tx) / 1e6
        self.stats.record_rx(lat_ms)
        self.stats.record_tx(len(msg.data))

    def check_done(self):
        if time.time() >= self.t_end:
            rclpy.shutdown()

def main():
    ap = argparse.ArgumentParser(description="ROS2 pub+sub demo using CompressedImage")
    ap.add_argument('--kind', choices=['rgb','tof'], default='rgb')
    ap.add_argument('--codec', choices=['jpeg','png','png16'], default='jpeg')
    ap.add_argument('--hz', type=float, default=30.0)
    ap.add_argument('--seconds', type=float, default=5.0)
    args = ap.parse_args()

    rclpy.init()
    stats = StreamStats()
    pub = Pub(args.kind, args.codec, args.hz, args.seconds)
    sub = Sub(stats, args.seconds)

    ex = rclpy.executors.MultiThreadedExecutor()
    ex.add_node(pub); ex.add_node(sub)
    try:
        ex.spin()
    finally:
        ex.shutdown()
        pub.destroy_node(); sub.destroy_node()

    # summary
    from rich.console import Console
    from rich.table import Table
    console = Console()
    table = Table(title="ROS2 Stream Summary")
    s = stats.summary()
    for k in ["tx","rx","loss_pct","mb_tx","lat_ms_p50","lat_ms_p95","lat_ms_mean"]:
        table.add_row(k, str(s[k]))
    console.print(table)

if __name__ == '__main__':
    main()
