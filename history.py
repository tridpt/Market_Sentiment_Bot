"""Lưu trữ và truy xuất lịch sử các lần phân tích để theo dõi xu hướng theo thời gian."""
import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def save_record(topic, result, source_count=0):
    """Lưu một bản ghi kết quả phân tích kèm timestamp."""
    _ensure_dir()
    records = load_all()
    record = {
        "topic": topic,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "tong_quan": result.get("tong_quan"),
        "phan_tram_tich_cuc": result.get("phan_tram_tich_cuc", 0),
        "phan_tram_tieu_cuc": result.get("phan_tram_tieu_cuc", 0),
        "phan_tram_trung_lap": result.get("phan_tram_trung_lap", 0),
        "source_count": source_count,
        "full_result": result,
    }
    records.append(record)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return record


def load_all():
    """Đọc toàn bộ lịch sử. Trả về list rỗng nếu chưa có."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def get_history_for_topic(topic):
    """Lấy các bản ghi của một chủ đề (không phân biệt hoa thường), sắp theo thời gian."""
    topic_l = topic.strip().lower()
    records = [r for r in load_all() if r.get("topic", "").strip().lower() == topic_l]
    records.sort(key=lambda r: r.get("timestamp", ""))
    return records


def list_topics():
    """Liệt kê các chủ đề đã từng phân tích kèm số lần."""
    counts = {}
    for r in load_all():
        t = r.get("topic", "")
        counts[t] = counts.get(t, 0) + 1
    return counts
