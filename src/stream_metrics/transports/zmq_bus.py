from __future__ import annotations
from dataclasses import dataclass
import time
import zmq

@dataclass
class Packet:
    ts_ns: int
    payload: bytes

class ZmqBus:
    def __init__(self, endpoint: str = "tcp://127.0.0.1:5556"):
        self.ctx = zmq.Context.instance()
        # PUB
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(endpoint)
        # Allow bind to settle before connecting SUB in same process
        time.sleep(0.1)
        # SUB
        self.sub = self.ctx.socket(zmq.SUB)
        self.sub.connect(endpoint)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"")
        self.poller = zmq.Poller()
        self.poller.register(self.sub, zmq.POLLIN)

    def publish(self, pkt: Packet) -> None:
        # [topic empty][ts][payload]
        self.pub.send_multipart([b"", str(pkt.ts_ns).encode("ascii"), pkt.payload])

    def subscribe(self, timeout: float | None = 1.0) -> Packet | None:
        to_ms = 0 if timeout is None else int(max(0.0, timeout) * 1000)
        events = dict(self.poller.poll(to_ms))
        if self.sub not in events:
            return None
        _topic, ts_b, payload = self.sub.recv_multipart()
        return Packet(ts_ns=int(ts_b.decode("ascii")), payload=payload)
