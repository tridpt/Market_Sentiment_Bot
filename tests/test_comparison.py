"""Test cho tính năng so sánh nhiều chủ đề (parse_topics + run_comparison + format).
Dùng mock, KHÔNG gọi API thật."""
import engine
import reporter


SAMPLE_A = {
    "tong_quan": "Tích Cực",
    "phan_tram_tich_cuc": 70, "phan_tram_tieu_cuc": 15, "phan_tram_trung_lap": 15,
    "top_3_khen": ["a", "b", "c"], "top_3_che": ["x", "y", "z"],
    "ket_luan_ngan": "Tốt.",
}
SAMPLE_B = {
    "tong_quan": "Tiêu Cực",
    "phan_tram_tich_cuc": 30, "phan_tram_tieu_cuc": 55, "phan_tram_trung_lap": 15,
    "top_3_khen": ["d", "e", "f"], "top_3_che": ["m", "n", "p"],
    "ket_luan_ngan": "Tệ.",
}


# ---------- parse_topics ----------

def test_parse_vs():
    assert engine.parse_topics("iPhone vs Samsung") == ["iPhone", "Samsung"]


def test_parse_versus():
    assert engine.parse_topics("Tesla versus VinFast") == ["Tesla", "VinFast"]


def test_parse_vietnamese_voi():
    assert engine.parse_topics("Honda với Yamaha") == ["Honda", "Yamaha"]


def test_parse_comma():
    assert engine.parse_topics("A, B, C") == ["A", "B", "C"]


def test_parse_single():
    assert engine.parse_topics("iPhone 15") == ["iPhone 15"]


def test_parse_empty():
    assert engine.parse_topics("") == []


def test_parse_vs_inside_word_not_split():
    # 'vs' phải là từ riêng (có khoảng trắng), không tách giữa chữ
    assert engine.parse_topics("Verstappen") == ["Verstappen"]


# ---------- run_comparison ----------

def setup_function():
    engine.clear_cache()


def _patch_two(monkeypatch):
    results = {"iphone": SAMPLE_A, "samsung": SAMPLE_B}
    monkeypatch.setattr(engine, "fetch_market_data", lambda topic, limit=50: ["tin 1", "tin 2"])
    monkeypatch.setattr(engine, "analyze_sentiment",
                        lambda topic, lst: results.get(topic.strip().lower(), SAMPLE_A))
    monkeypatch.setattr(engine.history, "save_record", lambda *a, **k: None)


def test_run_comparison_ok(monkeypatch):
    _patch_two(monkeypatch)
    res = engine.run_comparison("iPhone vs Samsung", save_history=False)
    assert res["ok"] is True
    assert len(res["items"]) == 2
    assert res["items"][0]["topic"] == "iPhone"
    assert res["items"][0]["result"]["phan_tram_tich_cuc"] == 70


def test_run_comparison_needs_two():
    res = engine.run_comparison("iPhone", save_history=False)
    assert res["ok"] is False
    assert "ít nhất 2" in res["error"]


def test_run_comparison_dedupe(monkeypatch):
    _patch_two(monkeypatch)
    res = engine.run_comparison("iPhone vs iphone vs Samsung", save_history=False)
    # 'iPhone' và 'iphone' trùng -> còn 2 chủ đề
    assert len(res["items"]) == 2


def test_run_comparison_accepts_list(monkeypatch):
    _patch_two(monkeypatch)
    res = engine.run_comparison(["iPhone", "Samsung"], save_history=False)
    assert res["ok"] is True


def test_run_comparison_partial_failure(monkeypatch):
    # 1 chủ đề không có dữ liệu -> vẫn cần >= 2 thành công mới ok
    def fetch(topic, limit=50):
        return [] if topic.strip().lower() == "samsung" else ["tin"]
    monkeypatch.setattr(engine, "fetch_market_data", fetch)
    monkeypatch.setattr(engine, "analyze_sentiment", lambda t, l: SAMPLE_A)
    monkeypatch.setattr(engine.history, "save_record", lambda *a, **k: None)
    res = engine.run_comparison("iPhone vs Samsung", save_history=False)
    assert res["ok"] is False  # chỉ 1 thành công


# ---------- format so sánh ----------

def test_format_comparison_text():
    items = [
        {"topic": "iPhone", "ok": True, "result": SAMPLE_A, "source_count": 10},
        {"topic": "Samsung", "ok": True, "result": SAMPLE_B, "source_count": 8},
    ]
    out = reporter.format_comparison_text(items)
    assert "IPHONE" in out and "SAMSUNG" in out
    assert "70%" in out and "55%" in out
    # iPhone tích cực hơn -> là quán quân
    assert "IPHONE" in out.split("Dư luận tích cực nhất")[1]


def test_format_comparison_telegram_has_winner():
    items = [
        {"topic": "iPhone", "ok": True, "result": SAMPLE_A, "source_count": 10},
        {"topic": "Samsung", "ok": True, "result": SAMPLE_B, "source_count": 8},
    ]
    out = reporter.format_comparison_telegram(items)
    assert "<b>" in out
    assert "Tích cực nhất" in out
    assert "IPHONE" in out


def test_format_comparison_text_with_error_item():
    items = [
        {"topic": "iPhone", "ok": True, "result": SAMPLE_A, "source_count": 10},
        {"topic": "Hiem", "ok": False, "result": None, "error": "Không cào được dữ liệu"},
    ]
    out = reporter.format_comparison_text(items)
    assert "Hiem" in out and "Không cào được" in out
