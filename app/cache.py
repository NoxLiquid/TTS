import threading
from collections import OrderedDict


class LruCache:
    def __init__(self, capacity: int):
        self.capacity = max(0, capacity)
        self._data: "OrderedDict[str, bytes]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str):
        if self.capacity == 0:
            return None
        with self._lock:
            if key not in self._data:
                return None
            self._data.move_to_end(key)
            return self._data[key]

    def put(self, key: str, value: bytes):
        if self.capacity == 0:
            return
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            while len(self._data) > self.capacity:
                self._data.popitem(last=False)
