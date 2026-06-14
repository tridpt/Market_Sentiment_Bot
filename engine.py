"""Lõi xử lý dùng chung: cào dữ liệu -> phân tích AI -> lưu lịch sử.
Được gọi bởi CLI (main.py), Telegram bot (bot.py) và Web UI (webapp.py).
"""
import time

from scraper import fetch_market_data
from analyzer import analyze_sentiment
import history

# Cache kết quả theo chủ đề để tiết kiệm quota Gemini + tăng tốc.
# Quét lại cùng chủ đề trong vòng CACHE_TTL giây sẽ trả về kết quả đã lưu.
CACHE_TTL = 600  # 10 phút
_cache = {}  # { "topic_lower": {"ts": float, "data": dict} }


def clear_cache():
    """Xóa toàn bộ cache (hữu ích cho test hoặc khi muốn ép quét mới)."""
    _cache.clear()


def _cache_get(topic):
    """Trả về kết quả còn hạn trong cache, hoặc None nếu hết hạn/không có."""
    entry = _cache.get(topic.strip().lower())
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(topic, data):
    _cache[topic.strip().lower()] = {"ts": time.time(), "data": data}


def run_analysis(topic, limit=50, save_history=True, use_cache=True):
    """
    Chạy toàn bộ pipeline cho một chủ đề.
    Trả về dict: {ok, result, source_count, error, cached}.
    """
    topic = (topic or "").strip()
    if not topic:
        return {"ok": False, "error": "Chưa nhập chủ đề.", "result": None,
                "source_count": 0, "cached": False}

    # 1) Thử lấy từ cache trước
    if use_cache:
        cached = _cache_get(topic)
        if cached is not None:
            return {**cached, "cached": True}

    # 2) Cào dữ liệu
    data_list = fetch_market_data(topic, limit=limit)
    if not data_list:
        return {"ok": False, "error": "Không cào được dữ liệu nào cho chủ đề này.",
                "result": None, "source_count": 0, "cached": False}

    # 3) Phân tích AI
    result = analyze_sentiment(topic, data_list)
    if not result or "error" in result:
        return {"ok": False, "error": "AI phân tích thất bại (máy chủ lỗi hoặc quá tải).",
                "result": None, "source_count": len(data_list), "cached": False}

    outcome = {"ok": True, "error": None, "result": result,
               "source_count": len(data_list)}

    # 4) Lưu lịch sử
    if save_history:
        try:
            history.save_record(topic, result, source_count=len(data_list))
        except Exception:
            pass  # lưu lịch sử lỗi không nên làm hỏng cả pipeline

    # 5) Lưu cache
    if use_cache:
        _cache_set(topic, outcome)

    return {**outcome, "cached": False}
