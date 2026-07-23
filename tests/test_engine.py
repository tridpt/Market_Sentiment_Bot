"""Test cho engine.py - pipeline + cache. Dùng mock, KHÔNG gọi API thật."""
import engine


SAMPLE_RESULT = {
    "tong_quan": "Tích Cực",
    "phan_tram_tich_cuc": 70,
    "phan_tram_tieu_cuc": 15,
    "phan_tram_trung_lap": 15,
    "top_3_khen": ["a", "b", "c"],
    "top_3_che": ["x", "y", "z"],
    "ket_luan_ngan": "Tốt.",
}


def _patch(monkeypatch, data=None, result=None, save_spy=None):
    """Thay scraper/analyzer/history bằng hàm giả."""
    data = ["tin 1", "tin 2", "tin 3"] if data is None else data
    monkeypatch.setattr(engine, "fetch_market_data",
                        lambda topic, limit=50, time_range=None: data)
    monkeypatch.setattr(engine, "analyze_sentiment",
                        lambda topic, lst: result if result is not None else SAMPLE_RESULT)
    if save_spy is not None:
        monkeypatch.setattr(engine.history, "save_record", save_spy)
    else:
        monkeypatch.setattr(engine.history, "save_record", lambda *a, **k: None)


def setup_function():
    engine.clear_cache()


def test_empty_topic():
    res = engine.run_analysis("   ", save_history=False)
    assert res["ok"] is False
    assert "Chưa nhập" in res["error"]


def test_successful_analysis(monkeypatch):
    _patch(monkeypatch)
    res = engine.run_analysis("iPhone", save_history=False, use_cache=False)
    assert res["ok"] is True
    assert res["result"]["phan_tram_tich_cuc"] == 70
    assert res["source_count"] == 3
    assert res["cached"] is False


def test_no_data(monkeypatch):
    _patch(monkeypatch, data=[])
    res = engine.run_analysis("chu de hiem", save_history=False)
    assert res["ok"] is False
    assert "Không cào được" in res["error"]


def test_ai_failure(monkeypatch):
    _patch(monkeypatch, result={"error": "boom"})
    res = engine.run_analysis("iPhone", save_history=False)
    assert res["ok"] is False
    assert "thất bại" in res["error"]


def test_cache_hit(monkeypatch):
    calls = {"n": 0}

    def counting_fetch(topic, limit=50, time_range=None):
        calls["n"] += 1
        return ["a", "b"]

    monkeypatch.setattr(engine, "fetch_market_data", counting_fetch)
    monkeypatch.setattr(engine, "analyze_sentiment", lambda t, l: SAMPLE_RESULT)
    monkeypatch.setattr(engine.history, "save_record", lambda *a, **k: None)

    first = engine.run_analysis("Tesla", save_history=False)
    assert first["cached"] is False
    second = engine.run_analysis("Tesla", save_history=False)
    assert second["cached"] is True
    # Lần 2 lấy từ cache nên không gọi fetch lần nữa
    assert calls["n"] == 1


def test_cache_case_insensitive(monkeypatch):
    _patch(monkeypatch)
    engine.run_analysis("Tesla", save_history=False)
    res = engine.run_analysis("tesla", save_history=False)
    assert res["cached"] is True


def test_cache_disabled(monkeypatch):
    calls = {"n": 0}

    def counting_fetch(topic, limit=50, time_range=None):
        calls["n"] += 1
        return ["a"]

    monkeypatch.setattr(engine, "fetch_market_data", counting_fetch)
    monkeypatch.setattr(engine, "analyze_sentiment", lambda t, l: SAMPLE_RESULT)
    monkeypatch.setattr(engine.history, "save_record", lambda *a, **k: None)

    engine.run_analysis("Tesla", save_history=False, use_cache=False)
    engine.run_analysis("Tesla", save_history=False, use_cache=False)
    assert calls["n"] == 2


def test_cache_expiry(monkeypatch):
    _patch(monkeypatch)
    monkeypatch.setattr(engine, "CACHE_TTL", 0)  # hết hạn ngay lập tức
    engine.run_analysis("Tesla", save_history=False)
    res = engine.run_analysis("Tesla", save_history=False)
    assert res["cached"] is False


def test_save_history_called(monkeypatch):
    spy = {"called": 0}

    def fake_save(topic, result, source_count=0):
        spy["called"] += 1

    _patch(monkeypatch, save_spy=fake_save)
    engine.run_analysis("iPhone", save_history=True)
    assert spy["called"] == 1


# ---------- trích nguồn (sources) ----------

def test_sources_extracted_and_attached(monkeypatch):
    data = [
        {"text": "tin 1", "url": "https://a.com/1", "title": "Bài 1", "source": "Hacker News"},
        {"text": "tin 2", "url": "https://b.com/2", "title": "Bài 2", "source": "Google News"},
        {"text": "tin 3", "url": None, "title": "x", "source": "Reddit"},  # thiếu url -> bỏ
    ]
    monkeypatch.setattr(engine, "fetch_market_data",
                        lambda topic, limit=50, time_range=None: data)
    monkeypatch.setattr(engine, "analyze_sentiment", lambda topic, texts: dict(SAMPLE_RESULT))
    monkeypatch.setattr(engine.history, "save_record", lambda *a, **k: None)

    res = engine.run_analysis("iPhone", save_history=False, use_cache=False)
    assert res["ok"] is True
    assert len(res["sources"]) == 2
    assert res["sources"][0]["url"] == "https://a.com/1"
    # Nguồn cũng được đính vào result cho reporter dùng
    assert res["result"]["_sources"] == res["sources"]


def test_analyze_receives_plain_text_not_dicts(monkeypatch):
    captured = {}
    data = [{"text": "hello world data dai hon 20 ky tu", "url": "u", "title": "t", "source": "s"}]
    monkeypatch.setattr(engine, "fetch_market_data",
                        lambda topic, limit=50, time_range=None: data)

    def fake_analyze(topic, texts):
        captured["texts"] = texts
        return dict(SAMPLE_RESULT)

    monkeypatch.setattr(engine, "analyze_sentiment", fake_analyze)
    monkeypatch.setattr(engine.history, "save_record", lambda *a, **k: None)

    engine.run_analysis("x", save_history=False, use_cache=False)
    assert captured["texts"] == ["hello world data dai hon 20 ky tu"]


def test_sources_deduped_by_url(monkeypatch):
    data = [
        {"text": "a", "url": "https://same.com", "title": "A", "source": "HN"},
        {"text": "b", "url": "https://same.com", "title": "B", "source": "GN"},  # trùng url
    ]
    monkeypatch.setattr(engine, "fetch_market_data",
                        lambda topic, limit=50, time_range=None: data)
    monkeypatch.setattr(engine, "analyze_sentiment", lambda topic, texts: dict(SAMPLE_RESULT))
    monkeypatch.setattr(engine.history, "save_record", lambda *a, **k: None)

    res = engine.run_analysis("t", save_history=False, use_cache=False)
    assert len(res["sources"]) == 1


def test_time_range_in_cache_key(monkeypatch):
    calls = {"n": 0}

    def counting_fetch(topic, limit=50, time_range=None):
        calls["n"] += 1
        return ["a", "b"]

    monkeypatch.setattr(engine, "fetch_market_data", counting_fetch)
    monkeypatch.setattr(engine, "analyze_sentiment", lambda t, texts: dict(SAMPLE_RESULT))
    monkeypatch.setattr(engine.history, "save_record", lambda *a, **k: None)

    # Khác time_range -> khác cache key -> phải fetch lại
    engine.run_analysis("Tesla", time_range="week", save_history=False)
    engine.run_analysis("Tesla", time_range="month", save_history=False)
    assert calls["n"] == 2
    # Lặp lại cùng time_range -> cache hit, không fetch thêm
    res = engine.run_analysis("Tesla", time_range="week", save_history=False)
    assert res["cached"] is True
    assert calls["n"] == 2


def test_time_range_passed_to_fetch(monkeypatch):
    captured = {}

    def fetch(topic, limit=50, time_range=None):
        captured["time_range"] = time_range
        return ["tin dai hon 20 ky tu de qua filter"]

    monkeypatch.setattr(engine, "fetch_market_data", fetch)
    monkeypatch.setattr(engine, "analyze_sentiment", lambda t, texts: dict(SAMPLE_RESULT))
    monkeypatch.setattr(engine.history, "save_record", lambda *a, **k: None)

    engine.run_analysis("x", time_range="year", save_history=False, use_cache=False)
    assert captured["time_range"] == "year"
