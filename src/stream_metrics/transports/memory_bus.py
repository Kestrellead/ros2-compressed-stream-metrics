from __future__ import annotations
from dataclasses import dataclass
from collections import deque
import threading

@dataclass
class Packet:
    ts_ns: int
    payload: bytes

class MemoryBus:
    def __init__(self, maxlen: int = 1024):
        self.q = deque(maxlen=maxlen)
        self.cv = threading.Condition()

    def publish(self, pkt: Packet) -> None:
        with self.cv:
            self.q.append(pkt)
            self.cv.notify()

    def subscribe(self, timeout: float | None = 1.0) -> Packet | None:
        with self.cv:
            if not self.q:
                self.cv.wait(timeout=timeout)
            return self.q.popleft() if self.q else None
