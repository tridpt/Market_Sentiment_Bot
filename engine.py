"""Lõi xử lý dùng chung: cào dữ liệu -> phân tích AI -> lưu lịch sử.
Được gọi bởi CLI (main.py), Telegram bot (bot.py) và Web UI (webapp.py).
"""
from scraper import fetch_market_data
from analyzer import analyze_sentiment
import history


def run_analysis(topic, limit=50, save_history=True):
    """
    Chạy toàn bộ pipeline cho một chủ đề.
    Trả về dict: {ok, result, source_count, error}.
    """
    topic = (topic or "").strip()
    if not topic:
        return {"ok": False, "error": "Chưa nhập chủ đề.", "result": None, "source_count": 0}

    data_list = fetch_market_data(topic, limit=limit)
    if not data_list:
        return {"ok": False, "error": "Không cào được dữ liệu nào cho chủ đề này.",
                "result": None, "source_count": 0}

    result = analyze_sentiment(topic, data_list)
    if not result or "error" in result:
        return {"ok": False, "error": "AI phân tích thất bại (máy chủ lỗi hoặc quá tải).",
                "result": None, "source_count": len(data_list)}

    if save_history:
        try:
            history.save_record(topic, result, source_count=len(data_list))
        except Exception:
            pass  # lưu lịch sử lỗi không nên làm hỏng cả pipeline

    return {"ok": True, "error": None, "result": result, "source_count": len(data_list)}
