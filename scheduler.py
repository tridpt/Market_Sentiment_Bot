"""Bộ quét theo lịch: định kỳ phân tích một danh sách chủ đề để tích lũy dữ liệu xu hướng.

Chạy nền độc lập: `python scheduler.py`
Cấu hình qua .env:
  SCHEDULED_TOPICS="iPhone 15, VinFast, Tesla"   # danh sách chủ đề, cách nhau dấu phẩy
  SCAN_INTERVAL_HOURS="24"                         # chu kỳ quét (giờ)
  SCAN_TIME_RANGE="week"                           # lọc độ mới: week/month/year (bỏ trống = không lọc)
  SCHEDULED_CHAT_ID="123456789"                    # (tùy chọn) gửi tóm tắt qua Telegram
"""
import os
import html
import time
import requests
from dotenv import load_dotenv

from engine import run_analysis

load_dotenv()


def _parse_topics_env(raw):
    """Tách danh sách chủ đề từ biến môi trường (cách nhau dấu phẩy)."""
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def telegram_notify(text):
    """Gửi tin nhắn tới Telegram nếu có TELEGRAM_BOT_TOKEN + SCHEDULED_CHAT_ID.

    Trả về True nếu gửi thành công, False nếu chưa cấu hình hoặc lỗi.
    Dùng Bot API trực tiếp (requests) để không phải chạy vòng lặp async của bot.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("SCHEDULED_CHAT_ID")
    if not token or not chat_id:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=20,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[!] ⚠️ Không gửi được thông báo Telegram: {e}")
        return False


def _format_summary(results, time_range=None):
    """Định dạng tóm tắt một lượt quét thành HTML cho Telegram."""
    lines = ["📅 <b>Báo cáo quét định kỳ</b>"]
    if time_range:
        lines.append(f"<i>Khoảng thời gian: {html.escape(str(time_range))}</i>")
    for r in results:
        safe_topic = html.escape(str(r.get("topic", "")))
        if r["ok"]:
            safe_tq = html.escape(str(r.get("tong_quan", "")))
            lines.append(f"• {safe_topic}: {safe_tq} "
                         f"({r['phan_tram_tich_cuc']}% tích cực)")
        else:
            safe_err = html.escape(str(r.get("error", "")))
            lines.append(f"• {safe_topic}: ❌ {safe_err}")
    return "\n".join(lines)


def run_scheduled_scan(topics, time_range=None, notifier=None):
    """Quét một lượt cho tất cả `topics`, lưu lịch sử để dựng xu hướng.

    `use_cache=False` để mỗi lần quét lấy dữ liệu mới (điểm dữ liệu xu hướng khác nhau).
    Nếu truyền `notifier`, gọi nó với chuỗi tóm tắt sau khi quét xong.
    Trả về list summary mỗi chủ đề: {topic, ok, tong_quan, phan_tram_tich_cuc, error}.
    """
    results = []
    for topic in topics:
        res = run_analysis(topic, save_history=True, use_cache=False, time_range=time_range)
        result = res.get("result") or {}
        results.append({
            "topic": topic,
            "ok": res["ok"],
            "tong_quan": result.get("tong_quan"),
            "phan_tram_tich_cuc": result.get("phan_tram_tich_cuc"),
            "error": res.get("error"),
        })
    if notifier:
        notifier(_format_summary(results, time_range))
    return results


def main():
    topics = _parse_topics_env(os.getenv("SCHEDULED_TOPICS"))
    if not topics:
        print("[!] Chưa cấu hình SCHEDULED_TOPICS trong .env. Thoát.")
        return

    interval_h = float(os.getenv("SCAN_INTERVAL_HOURS", "24"))
    time_range = os.getenv("SCAN_TIME_RANGE") or None

    print(f"⏰ Scheduler chạy: {len(topics)} chủ đề, mỗi {interval_h} giờ. (Ctrl+C để dừng)")
    while True:
        print(f"\n[*] Bắt đầu quét {len(topics)} chủ đề...")
        try:
            run_scheduled_scan(topics, time_range=time_range, notifier=telegram_notify)
        except Exception as e:
            print(f"[!] ⚠️ Lỗi trong lượt quét: {e}")
        print(f"[+] Xong. Ngủ {interval_h} giờ.")
        time.sleep(interval_h * 3600)


if __name__ == "__main__":
    main()
