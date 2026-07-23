"""Hàng đợi job chạy nền đơn giản (in-process) cho Web UI.

Mục tiêu: không để request HTTP bị khóa trong lúc cào dữ liệu + gọi AI (có thể mất
hàng chục giây). Request chỉ tạo job rồi trả ngay job_id; client poll trạng thái sau.

Lưu ý: đây là hàng đợi trong tiến trình (dùng ThreadPoolExecutor). Nếu chạy nhiều
process/worker (gunicorn -w >1) thì state không chia sẻ — khi đó cần Redis/RQ/Celery.
Với dev server 1 tiến trình thì đủ dùng và loại bỏ được việc block request.
"""
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor


class JobManager:
    """Quản lý vòng đời job: queued -> running -> done/error."""

    def __init__(self, max_workers=2, ttl=1800):
        # Giới hạn số job chạy đồng thời -> chặn một client làm ngộp tài nguyên.
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._jobs = {}
        self._lock = threading.Lock()
        self._ttl = ttl  # job giữ tối đa bao lâu (giây) trước khi bị dọn

    def submit(self, fn, *args, **kwargs):
        """Đưa một hàm vào chạy nền. Trả về job_id."""
        job_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._cleanup_locked()
            self._jobs[job_id] = {
                "status": "queued", "result": None,
                "error": None, "created": time.time(),
            }
        self._executor.submit(self._run, job_id, fn, args, kwargs)
        return job_id

    def _run(self, job_id, fn, args, kwargs):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "running"
        try:
            result = fn(*args, **kwargs)
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id].update(status="done", result=result)
        except Exception as e:  # noqa: BLE001 - job không được làm sập worker
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id].update(status="error", error=str(e))

    def get(self, job_id):
        """Trả về bản sao trạng thái job, hoặc None nếu không tồn tại."""
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def _cleanup_locked(self):
        """Xóa các job quá hạn để dict không phình mãi. Gọi khi đang giữ lock."""
        now = time.time()
        expired = [k for k, v in self._jobs.items() if now - v["created"] > self._ttl]
        for k in expired:
            del self._jobs[k]
