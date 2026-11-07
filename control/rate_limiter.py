"""Control helper: at most N chat messages per user per hour (kept in memory).

In-memory is fine for a class demo. On Vercel each cold start resets it; for
a stricter limit, store the timestamps in the database instead.
"""
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, limit=20, window_seconds=3600, clock=time.monotonic):
        self.limit = limit
        self.window = window_seconds
        self.clock = clock
        self._hits = defaultdict(deque)

    def allow(self, key):
        now = self.clock()
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True
