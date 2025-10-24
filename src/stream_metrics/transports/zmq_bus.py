from __future__ import annotations
from typing import Optional
from .memory_bus import Packet  # reuse the same Packet(ts_ns, payload)

class ZmqBus:
    """
    ZeroMQ transport with lazy role selection.
    - First call to publish() => create PUB and bind() to endpoint
    - First call to subscribe() => create SUB and connect() to endpoint
    Endpoint is a single tcp://host:port string.
    """
    def __init__(self, endpoint: str = "tcp://127.0.0.1:5556"):
        self.endpoint = endpoint
        self._ctx = None
        self._sock = None
        self._role: Optional[str] = None  # "pub" or "sub"

    def _ensure_ctx(self):
        if self._ctx is None:
            import zmq  # optional dependency
            self._zmq = zmq
            self._ctx = zmq.Context.instance()

    def publish(self, pkt: Packet) -> None:
        self._ensure_ctx()
        if self._role is None:
            self._role = "pub"
            self._sock = self._zmq.Socket(self._ctx, self._zmq.PUB)
            # PUB must bind; SUB will connect
            self._sock.bind(self.endpoint)
        elif self._role != "pub":
            raise RuntimeError("ZmqBus is in SUB mode; cannot publish")
        # send [ts_ns(bytes), payload(bytes)]
        self._sock.send_multipart([str(pkt.ts_ns).encode("ascii"), pkt.payload])

    def subscribe(self, timeout: float | None = 1.0) -> Optional[Packet]:
        self._ensure_ctx()
        if self._role is None:
            self._role = "sub"
            self._sock = self._zmq.Socket(self._ctx, self._zmq.SUB)
            # SUB connects; subscribe to all
            self._sock.connect(self.endpoint)
            self._sock.setsockopt(self._zmq.SUBSCRIBE, b"")
        elif self._role != "sub":
            raise RuntimeError("ZmqBus is in PUB mode; cannot subscribe")
        if timeout is not None:
            self._sock.setsockopt(self._zmq.RCVTIMEO, int(timeout * 1000))
        try:
            ts_b, payload = self._sock.recv_multipart()
        except self._zmq.Again:
            return None
        ts_ns = int(ts_b.decode("ascii"))
        return Packet(ts_ns=ts_ns, payload=payload)
