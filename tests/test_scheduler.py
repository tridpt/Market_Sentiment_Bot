"""Test cho scheduler.py - quét định kỳ. Mock run_analysis, KHÔNG gọi API thật."""
import scheduler


def test_parse_topics_env():
    assert scheduler._parse_topics_env("iPhone, VinFast , Tesla") == ["iPhone", "VinFast", "Tesla"]
    assert scheduler._parse_topics_env("") == []
    assert scheduler._parse_topics_env(None) == []


def test_run_scheduled_scan_calls_analysis_per_topic(monkeypatch):
    calls = []

    def fake_analysis(topic, save_history=True, use_cache=False, time_range=None):
        calls.append((topic, save_history, use_cache, time_range))
        return {"ok": True, "result": {"tong_quan": "Tích Cực", "phan_tram_tich_cuc": 70},
                "error": None}

    monkeypatch.setattr(scheduler, "run_analysis", fake_analysis)
    results = scheduler.run_scheduled_scan(["iPhone", "Tesla"], time_range="week")

    assert len(results) == 2
    assert results[0]["topic"] == "iPhone"
    assert results[0]["tong_quan"] == "Tích Cực"
    # Quét định kỳ luôn lưu lịch sử và không dùng cache, truyền đúng time_range
    assert all(c[1] is True and c[2] is False and c[3] == "week" for c in calls)


def test_run_scheduled_scan_handles_failure(monkeypatch):
    monkeypatch.setattr(scheduler, "run_analysis",
                        lambda topic, save_history=True, use_cache=False, time_range=None: {
                            "ok": False, "result": None, "error": "Không cào được dữ liệu"})
    results = scheduler.run_scheduled_scan(["Hiem"])
    assert results[0]["ok"] is False
    assert results[0]["error"] == "Không cào được dữ liệu"


def test_run_scheduled_scan_calls_notifier(monkeypatch):
    monkeypatch.setattr(scheduler, "run_analysis",
                        lambda topic, save_history=True, use_cache=False, time_range=None: {
                            "ok": True, "result": {"tong_quan": "Tích Cực",
                                                   "phan_tram_tich_cuc": 60}, "error": None})
    sent = {}

    def fake_notifier(text):
        sent["text"] = text

    scheduler.run_scheduled_scan(["iPhone"], notifier=fake_notifier)
    assert "iPhone" in sent["text"]
    assert "Báo cáo quét định kỳ" in sent["text"]


def test_notifier_not_called_when_none(monkeypatch):
    # Không truyền notifier -> không lỗi, chỉ trả kết quả
    monkeypatch.setattr(scheduler, "run_analysis",
                        lambda topic, save_history=True, use_cache=False, time_range=None: {
                            "ok": True, "result": {"tong_quan": "x", "phan_tram_tich_cuc": 1},
                            "error": None})
    results = scheduler.run_scheduled_scan(["A"])
    assert len(results) == 1


def test_telegram_notify_skips_without_config(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("SCHEDULED_CHAT_ID", raising=False)
    assert scheduler.telegram_notify("hello") is False


def test_format_summary_includes_range():
    results = [{"topic": "iPhone", "ok": True, "tong_quan": "Tích Cực",
                "phan_tram_tich_cuc": 70, "error": None}]
    out = scheduler._format_summary(results, time_range="month")
    assert "month" in out
    assert "iPhone" in out
