"""Rate limiter đơn giản theo cửa sổ trượt (sliding window), an toàn đa luồng.

Dùng để giới hạn số yêu cầu tốn phí (tạo job phân tích) trên mỗi IP trong một
khoảng thời gian, tránh lạm dụng/DoS nhẹ. In-process như job queue.
"""
import time
import threading
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests=10, window=60):
        self.max_requests = max_requests
        self.window = window
        self._hits = defaultdict(deque)  # key -> deque[timestamp]
        self._lock = threading.Lock()

    def allow(self, key):
        """Ghi nhận 1 lượt cho `key`. Trả True nếu còn hạn ngạch, False nếu vượt."""
        now = time.time()
        with self._lock:
            dq = self._hits[key]
            # Bỏ các mốc thời gian đã ra khỏi cửa sổ
            while dq and now - dq[0] > self.window:
                dq.popleft()
            if len(dq) >= self.max_requests:
                return False
            dq.append(now)
            return True

    def retry_after(self, key):
        """Số giây ước lượng cần chờ trước khi được phép lại."""
        with self._lock:
            dq = self._hits[key]
            if not dq:
                return 0
            return max(0, int(self.window - (time.time() - dq[0])))
