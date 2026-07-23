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

# Số nguồn tối đa đính kèm báo cáo (trích dẫn link bài viết gốc).
MAX_SOURCES = 10


def _extract_sources(data_list):
    """Rút danh sách nguồn {title, url, source} từ dữ liệu cào được.

    Bỏ qua item không phải dict hoặc không có url (vd khi test mock trả về list str).
    Khử trùng lặp theo url, giữ thứ tự, giới hạn MAX_SOURCES.
    """
    seen = set()
    sources = []
    for item in data_list:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        sources.append({
            "title": item.get("title") or item.get("source") or "Nguồn",
            "url": url,
            "source": item.get("source"),
        })
        if len(sources) >= MAX_SOURCES:
            break
    return sources


def clear_cache():
    """Xóa toàn bộ cache (hữu ích cho test hoặc khi muốn ép quét mới)."""
    _cache.clear()


def _cache_key(topic, limit):
    """Cache key gồm cả topic lẫn limit vì limit khác nhau -> dữ liệu khác nhau."""
    return (topic.strip().lower(), int(limit))


def _cache_get(topic, limit):
    """Trả về kết quả còn hạn trong cache, hoặc None nếu hết hạn/không có."""
    entry = _cache.get(_cache_key(topic, limit))
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(topic, limit, data):
    _cache[_cache_key(topic, limit)] = {"ts": time.time(), "data": data}


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
        cached = _cache_get(topic, limit)
        if cached is not None:
            return {**cached, "cached": True}

    # 2) Cào dữ liệu
    data_list = fetch_market_data(topic, limit=limit)
    if not data_list:
        return {"ok": False, "error": "Không cào được dữ liệu nào cho chủ đề này.",
                "result": None, "source_count": 0, "cached": False}

    # Tách phần text cho AI (item có thể là dict {"text",...} hoặc str thuần)
    texts = [item["text"] if isinstance(item, dict) else item for item in data_list]
    sources = _extract_sources(data_list)

    # 3) Phân tích AI
    result = analyze_sentiment(topic, texts)
    if not result or "error" in result:
        return {"ok": False, "error": "AI phân tích thất bại (máy chủ lỗi hoặc quá tải).",
                "result": None, "source_count": len(texts), "cached": False}

    # Đính danh sách nguồn vào result để reporter/web hiển thị trích dẫn.
    result["_sources"] = sources

    outcome = {"ok": True, "error": None, "result": result,
               "source_count": len(texts), "sources": sources}

    # 4) Lưu lịch sử
    if save_history:
        try:
            history.save_record(topic, result, source_count=len(data_list))
        except Exception as e:
            # Lưu lịch sử lỗi không nên làm hỏng cả pipeline, nhưng phải log để còn biết.
            print(f"[!] ⚠️ Không lưu được lịch sử cho '{topic}': {e}")

    # 5) Lưu cache
    if use_cache:
        _cache_set(topic, limit, outcome)

    return {**outcome, "cached": False}


def parse_topics(text):
    """
    Tách chuỗi nhập thành danh sách chủ đề. Hỗ trợ các dấu phân tách:
    'vs', 'versus', 'với', dấu phẩy. VD: 'iPhone vs Samsung' -> ['iPhone', 'Samsung'].
    """
    import re
    if not text:
        return []
    parts = re.split(r"\s+vs\.?\s+|\s+versus\s+|\s+với\s+|,", text, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]


# Số chủ đề tối đa cho một lần so sánh (tránh một yêu cầu chạy quá nhiều pipeline tốn phí).
MAX_COMPARE_TOPICS = 4


def run_comparison(topics, limit=50, save_history=True, use_cache=True):
    """
    Phân tích nhiều chủ đề và gộp kết quả để so sánh.
    `topics` có thể là chuỗi ('iPhone vs Samsung') hoặc list.
    Trả về dict: {ok, items, error}. Mỗi item: {topic, ok, result, source_count, error}.
    """
    if isinstance(topics, str):
        topics = parse_topics(topics)
    # Khử trùng lặp giữ thứ tự
    seen = set()
    clean_topics = []
    for t in topics:
        key = t.strip().lower()
        if t.strip() and key not in seen:
            seen.add(key)
            clean_topics.append(t.strip())

    if len(clean_topics) < 2:
        return {"ok": False, "error": "Cần ít nhất 2 chủ đề để so sánh (VD: 'iPhone vs Samsung').",
                "items": []}

    if len(clean_topics) > MAX_COMPARE_TOPICS:
        return {"ok": False,
                "error": f"Chỉ so sánh tối đa {MAX_COMPARE_TOPICS} chủ đề mỗi lần "
                         f"(bạn nhập {len(clean_topics)}).",
                "items": []}

    items = []
    for topic in clean_topics:
        res = run_analysis(topic, limit=limit, save_history=save_history, use_cache=use_cache)
        items.append({
            "topic": topic,
            "ok": res["ok"],
            "result": res.get("result"),
            "source_count": res.get("source_count", 0),
            "error": res.get("error"),
        })

    ok_items = [it for it in items if it["ok"]]
    if len(ok_items) < 2:
        return {"ok": False,
                "error": "Không đủ dữ liệu để so sánh (cần ít nhất 2 chủ đề phân tích thành công).",
                "items": items}

    return {"ok": True, "error": None, "items": items}
