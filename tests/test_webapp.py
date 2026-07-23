"""Test cho webapp.py bằng Flask test client.

Web giờ chạy theo mô hình job nền: request tạo job rồi redirect sang /result/<id>.
Trong test ta thay job_manager bằng bản chạy INLINE (đồng bộ) để kết quả có ngay,
tránh phụ thuộc thread/timing. Mock engine + charts, KHÔNG gọi API/IO thật.
"""
import pytest

import webapp
from ratelimit import RateLimiter


SAMPLE = {
    "tong_quan": "Tích Cực",
    "phan_tram_tich_cuc": 70, "phan_tram_tieu_cuc": 15, "phan_tram_trung_lap": 15,
    "top_3_khen": ["khen1", "khen2", "khen3"],
    "top_3_che": ["che1", "che2", "che3"],
    "ket_luan_ngan": "Nhìn chung ổn.",
}


class InlineJobManager:
    """Job manager giả: chạy hàm ngay lập tức để test có kết quả tức thì."""

    def __init__(self):
        self._jobs = {}

    def submit(self, fn, *args, **kwargs):
        job_id = str(len(self._jobs) + 1)
        try:
            self._jobs[job_id] = {"status": "done", "result": fn(*args, **kwargs), "error": None}
        except Exception as e:  # noqa: BLE001
            self._jobs[job_id] = {"status": "error", "result": None, "error": str(e)}
        return job_id

    def get(self, job_id):
        job = self._jobs.get(job_id)
        return dict(job) if job else None


@pytest.fixture
def client():
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


@pytest.fixture(autouse=True)
def _setup(monkeypatch):
    """Chạy job inline, rate limit rộng rãi, và chặn mọi thao tác vẽ chart/đọc history."""
    monkeypatch.setattr(webapp, "job_manager", InlineJobManager())
    monkeypatch.setattr(webapp, "limiter", RateLimiter(max_requests=1000, window=60))
    monkeypatch.setattr(webapp.charts, "make_pie_chart", lambda t, r: "reports/charts/pie.png")
    monkeypatch.setattr(webapp.charts, "make_trend_chart", lambda t, recs: None)
    monkeypatch.setattr(webapp.charts, "make_comparison_chart", lambda items: None)
    monkeypatch.setattr(webapp.history, "get_history_for_topic", lambda t: [])


def test_index_empty_shows_form(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Market Sentiment Bot" in resp.get_data(as_text=True)


def test_index_topic_too_long(client):
    long_topic = "a" * (webapp.MAX_TOPIC_LEN + 5)
    resp = client.get("/", query_string={"topic": long_topic})
    assert resp.status_code == 200
    assert "quá dài" in resp.get_data(as_text=True)


def test_single_topic_success(client, monkeypatch):
    monkeypatch.setattr(webapp, "run_analysis",
                        lambda topic, limit=50, save_history=True: {
                            "ok": True, "result": SAMPLE, "source_count": 12,
                            "error": None, "cached": False,
                        })
    resp = client.get("/", query_string={"topic": "iPhone"}, follow_redirects=True)
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Tích Cực" in body
    assert "khen1" in body
    assert "12 đoạn dữ liệu" in body


def test_single_topic_failure(client, monkeypatch):
    monkeypatch.setattr(webapp, "run_analysis",
                        lambda topic, limit=50, save_history=True: {
                            "ok": False, "result": None, "source_count": 0,
                            "error": "Không cào được dữ liệu nào cho chủ đề này.",
                            "cached": False,
                        })
    resp = client.get("/", query_string={"topic": "chu de la"}, follow_redirects=True)
    assert "Không cào được" in resp.get_data(as_text=True)


def test_compare_too_many_topics(client):
    resp = client.get("/", query_string={"topic": "a vs b vs c vs d vs e"})
    assert f"tối đa {webapp.MAX_COMPARE_TOPICS}" in resp.get_data(as_text=True)


def test_compare_success(client, monkeypatch):
    items = [
        {"topic": "iPhone", "ok": True, "result": SAMPLE, "source_count": 10, "error": None},
        {"topic": "Samsung", "ok": True,
         "result": {**SAMPLE, "phan_tram_tich_cuc": 40}, "source_count": 8, "error": None},
    ]
    monkeypatch.setattr(webapp, "run_comparison",
                        lambda topics, limit=50, save_history=True: {
                            "ok": True, "items": items, "error": None,
                        })
    resp = client.get("/", query_string={"topic": "iPhone vs Samsung"}, follow_redirects=True)
    body = resp.get_data(as_text=True)
    assert "So sánh" in body
    assert "iPhone" in body and "Samsung" in body
    assert "iPhone (70%)" in body  # iPhone tích cực hơn -> quán quân


def test_rate_limit_exceeded(client, monkeypatch):
    # Giới hạn chặt: 1 request / cửa sổ -> request thứ 2 bị chặn 429
    monkeypatch.setattr(webapp, "limiter", RateLimiter(max_requests=1, window=60))
    monkeypatch.setattr(webapp, "run_analysis",
                        lambda topic, limit=50, save_history=True: {
                            "ok": True, "result": SAMPLE, "source_count": 1,
                            "error": None, "cached": False,
                        })
    first = client.get("/", query_string={"topic": "iPhone"})
    assert first.status_code == 302  # redirect sang /result/<id>
    second = client.get("/", query_string={"topic": "iPhone"})
    assert second.status_code == 429
    assert "quá nhanh" in second.get_data(as_text=True)


def test_result_not_found(client):
    resp = client.get("/result/khong-ton-tai")
    assert resp.status_code == 404
    assert "không tìm thấy" in resp.get_data(as_text=True).lower()


def test_api_status_not_found(client):
    resp = client.get("/api/status/khong-ton-tai")
    assert resp.status_code == 404
    assert resp.get_json()["status"] == "not_found"


def test_api_status_done(client):
    # Đưa 1 job đã hoàn tất vào manager rồi hỏi trạng thái
    job_id = webapp.job_manager.submit(lambda: {"kind": "single", "topic": "x", "error": None})
    resp = client.get(f"/api/status/{job_id}")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "done"
