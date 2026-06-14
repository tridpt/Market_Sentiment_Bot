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
    monkeypatch.setattr(engine, "fetch_market_data", lambda topic, limit=50: data)
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

    def counting_fetch(topic, limit=50):
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

    def counting_fetch(topic, limit=50):
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
