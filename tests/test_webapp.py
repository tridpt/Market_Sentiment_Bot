"""Test cho webapp.py bằng Flask test client. Mock engine + charts, KHÔNG gọi API/IO thật."""
import pytest

import webapp


SAMPLE = {
    "tong_quan": "Tích Cực",
    "phan_tram_tich_cuc": 70, "phan_tram_tieu_cuc": 15, "phan_tram_trung_lap": 15,
    "top_3_khen": ["khen1", "khen2", "khen3"],
    "top_3_che": ["che1", "che2", "che3"],
    "ket_luan_ngan": "Nhìn chung ổn.",
}


@pytest.fixture
def client():
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


@pytest.fixture(autouse=True)
def _stub_charts(monkeypatch):
    """Chặn mọi thao tác vẽ biểu đồ / đọc history để test không đụng filesystem."""
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
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "quá dài" in body


def test_single_topic_success(client, monkeypatch):
    monkeypatch.setattr(webapp, "run_analysis",
                        lambda topic, limit=50, save_history=True: {
                            "ok": True, "result": SAMPLE, "source_count": 12,
                            "error": None, "cached": False,
                        })
    resp = client.get("/", query_string={"topic": "iPhone"})
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
    resp = client.get("/", query_string={"topic": "chu de la"})
    body = resp.get_data(as_text=True)
    assert "Không cào được" in body


def test_compare_too_many_topics(client):
    resp = client.get("/", query_string={"topic": "a vs b vs c vs d vs e"})
    body = resp.get_data(as_text=True)
    assert f"tối đa {webapp.MAX_COMPARE_TOPICS}" in body


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
    resp = client.get("/", query_string={"topic": "iPhone vs Samsung"})
    body = resp.get_data(as_text=True)
    assert "So sánh" in body
    assert "iPhone" in body and "Samsung" in body
    # iPhone (70%) tích cực hơn -> là quán quân
    assert "iPhone (70%)" in body
