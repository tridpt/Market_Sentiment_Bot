"""CLI: phân tích tâm lý thị trường từ terminal, có xuất báo cáo + biểu đồ."""
import sys

# Ép stdout/stderr về UTF-8 để emoji không làm crash khi chạy/pipe trên Windows (cp1252)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

from engine import run_analysis, run_comparison, parse_topics
from reporter import (format_text, save_report,
                      format_comparison_text)
from charts import make_pie_chart, make_trend_chart, make_comparison_chart
import history


def run_compare_cli(topics):
    """Chế độ so sánh nhiều chủ đề."""
    print(f"\n[*] So sánh {len(topics)} chủ đề: {', '.join(topics)}\n")
    res = run_comparison(topics, limit=50)
    if not res["ok"]:
        print(f"\n[!] {res['error']}")
        return
    print("\n\n" + format_comparison_text(res["items"]))
    try:
        chart = make_comparison_chart(res["items"])
        if chart:
            print(f"\n📊 Biểu đồ so sánh: {chart}")
    except Exception as e:
        print(f"[!] Không vẽ được biểu đồ so sánh: {e}")
    print("\n✨ Hoàn tất so sánh! ✨")


def main():
    print("=" * 60)
    print("🚀 HỆ THỐNG PHÂN TÍCH TÂM LÝ THỊ TRƯỜNG (DÙNG AI) 🚀")
    print("=" * 60)
    print("(Mẹo: nhập 'iPhone vs Samsung' để so sánh nhiều chủ đề)")
    print()

    topic = input("Nhập sản phẩm/chủ đề bạn muốn soi (VD: Cybertruck, iPhone 15...): ").strip()
    if not topic:
        print("Chưa nhập chủ đề, tự động thoát.")
        return

    # Nếu nhập nhiều chủ đề (vs / phẩy) -> chế độ so sánh
    parsed = parse_topics(topic)
    if len(parsed) >= 2:
        run_compare_cli(parsed)
        return

    print(f"\n[BƯỚC 1] BẮT ĐẦU ĐÀO DỮ LIỆU TỪ TIN TỨC & DIỄN ĐÀN (Hacker News + Google News)...")
    print("[BƯỚC 2] TRUYỀN DỮ LIỆU CHO BỘ NÃO MÁY GEMINI...\n")

    res = run_analysis(topic, limit=50)
    if not res["ok"]:
        print(f"\n[!] {res['error']}")
        return

    result = res["result"]

    # In báo cáo
    print("\n\n" + format_text(topic, result))

    # Xuất file Markdown + JSON
    md_path = save_report(topic, result, fmt="md")
    json_path = save_report(topic, result, fmt="json")
    print(f"\n📄 Đã lưu báo cáo: {md_path}")
    print(f"📄 Đã lưu JSON:    {json_path}")

    # Vẽ biểu đồ tròn
    try:
        pie = make_pie_chart(topic, result)
        print(f"📈 Biểu đồ tròn:   {pie}")
    except Exception as e:
        print(f"[!] Không vẽ được biểu đồ tròn: {e}")

    # Vẽ biểu đồ xu hướng nếu đã có >= 2 lần phân tích cùng chủ đề
    records = history.get_history_for_topic(topic)
    if len(records) >= 2:
        try:
            trend = make_trend_chart(topic, records)
            print(f"📉 Biểu đồ xu hướng: {trend}")
        except Exception as e:
            print(f"[!] Không vẽ được biểu đồ xu hướng: {e}")

    print("\n✨ Hoàn tất báo cáo! ✨")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã hủy chương trình.")
