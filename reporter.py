"""Định dạng và xuất báo cáo phân tích tâm lý ra nhiều dạng: text, Markdown, JSON."""
import os
import json
import re
from datetime import datetime

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")


def _ensure_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def _slug(text):
    """Biến chủ đề thành tên file an toàn."""
    s = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    s = re.sub(r"[\s]+", "_", s)
    return s or "report"


def format_text(topic, result):
    """Tạo báo cáo dạng text thuần (cho terminal)."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"📊 BẢNG BÁO CÁO CẢM XÚC THỊ TRƯỜNG: {topic.upper()} 📊")
    lines.append("=" * 60)
    lines.append(f">> THÁI ĐỘ TỔNG QUAN: {str(result.get('tong_quan', 'Không rõ')).upper()}")
    tc = result.get("phan_tram_tich_cuc", 0)
    tieu = result.get("phan_tram_tieu_cuc", 0)
    tl = result.get("phan_tram_trung_lap", 0)
    lines.append(f">> TỶ LỆ DƯ LUẬN: Tích cực ({tc}%) | Tiêu cực ({tieu}%) | Trung lập ({tl}%)")
    lines.append("\n✅ TOP 3 ĐIỂM ĐƯỢC KHEN:")
    for i, k in enumerate(result.get("top_3_khen", [])):
        lines.append(f"  {i+1}. {k}")
    lines.append("\n❌ TOP 3 ĐIỂM BỊ CHÊ/BỨC XÚC:")
    for i, c in enumerate(result.get("top_3_che", [])):
        lines.append(f"  {i+1}. {c}")
    lines.append("\n💡 KẾT LUẬN CỦA CHUYÊN GIA AI:")
    lines.append(f"  {result.get('ket_luan_ngan', '...')}")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_markdown(topic, result):
    """Tạo báo cáo dạng Markdown."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tc = result.get("phan_tram_tich_cuc", 0)
    tieu = result.get("phan_tram_tieu_cuc", 0)
    tl = result.get("phan_tram_trung_lap", 0)
    md = []
    md.append(f"# 📊 Báo cáo cảm xúc thị trường: {topic}")
    md.append(f"\n*Tạo lúc: {now}*\n")
    md.append(f"**Thái độ tổng quan:** {result.get('tong_quan', 'Không rõ')}\n")
    md.append("## Tỷ lệ dư luận\n")
    md.append(f"- ✅ Tích cực: **{tc}%**")
    md.append(f"- ❌ Tiêu cực: **{tieu}%**")
    md.append(f"- ⚪ Trung lập: **{tl}%**\n")
    md.append("## ✅ Top 3 điểm được khen\n")
    for i, k in enumerate(result.get("top_3_khen", [])):
        md.append(f"{i+1}. {k}")
    md.append("\n## ❌ Top 3 điểm bị chê / bức xúc\n")
    for i, c in enumerate(result.get("top_3_che", [])):
        md.append(f"{i+1}. {c}")
    md.append("\n## 💡 Kết luận của chuyên gia AI\n")
    md.append(f"> {result.get('ket_luan_ngan', '...')}")
    return "\n".join(md)


def format_telegram(topic, result):
    """Tạo báo cáo dạng Markdown gọn cho Telegram (MarkdownV2-safe-ish, dùng HTML)."""
    tc = result.get("phan_tram_tich_cuc", 0)
    tieu = result.get("phan_tram_tieu_cuc", 0)
    tl = result.get("phan_tram_trung_lap", 0)
    out = []
    out.append(f"📊 <b>BÁO CÁO CẢM XÚC: {topic.upper()}</b>")
    out.append(f"\n<b>Thái độ tổng quan:</b> {result.get('tong_quan', 'Không rõ')}")
    out.append(f"\n<b>Tỷ lệ dư luận:</b>")
    out.append(f"✅ Tích cực: {tc}%")
    out.append(f"❌ Tiêu cực: {tieu}%")
    out.append(f"⚪ Trung lập: {tl}%")
    out.append("\n<b>✅ Top điểm được khen:</b>")
    for i, k in enumerate(result.get("top_3_khen", [])):
        out.append(f"{i+1}. {k}")
    out.append("\n<b>❌ Top điểm bị chê:</b>")
    for i, c in enumerate(result.get("top_3_che", [])):
        out.append(f"{i+1}. {c}")
    out.append(f"\n💡 <b>Kết luận:</b>\n{result.get('ket_luan_ngan', '...')}")
    return "\n".join(out)


def save_report(topic, result, fmt="md"):
    """Lưu báo cáo ra file có timestamp. fmt = 'md' hoặc 'json'. Trả về đường dẫn file."""
    _ensure_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{_slug(topic)}_{ts}"
    if fmt == "json":
        path = os.path.join(REPORTS_DIR, base + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"topic": topic, "timestamp": ts, "result": result},
                      f, ensure_ascii=False, indent=2)
    else:
        path = os.path.join(REPORTS_DIR, base + ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(format_markdown(topic, result))
    return path


def format_comparison_text(items):
    """Báo cáo so sánh dạng text cho terminal. items: list {topic, ok, result, error}."""
    lines = []
    lines.append("=" * 60)
    lines.append("📊 BẢNG SO SÁNH CẢM XÚC THỊ TRƯỜNG 📊")
    lines.append("=" * 60)
    ok = [it for it in items if it.get("ok")]
    for it in items:
        if not it.get("ok"):
            lines.append(f"\n⚠️ {it['topic']}: {it.get('error', 'lỗi')}")
            continue
        r = it["result"]
        lines.append(f"\n▶ {it['topic'].upper()} ({it.get('source_count', 0)} nguồn)")
        lines.append(f"   Tổng quan: {r.get('tong_quan', '?')}")
        lines.append(f"   ✅ {r.get('phan_tram_tich_cuc', 0)}% | "
                     f"❌ {r.get('phan_tram_tieu_cuc', 0)}% | "
                     f"⚪ {r.get('phan_tram_trung_lap', 0)}%")

    # Kết luận: ai tích cực nhất
    if len(ok) >= 2:
        winner = max(ok, key=lambda it: it["result"].get("phan_tram_tich_cuc", 0))
        lines.append(f"\n🏆 Dư luận tích cực nhất: {winner['topic'].upper()} "
                     f"({winner['result'].get('phan_tram_tich_cuc', 0)}% tích cực)")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_comparison_telegram(items):
    """Báo cáo so sánh dạng HTML cho Telegram."""
    out = ["📊 <b>SO SÁNH CẢM XÚC THỊ TRƯỜNG</b>"]
    ok = [it for it in items if it.get("ok")]
    for it in items:
        if not it.get("ok"):
            out.append(f"\n⚠️ <b>{it['topic']}</b>: {it.get('error', 'lỗi')}")
            continue
        r = it["result"]
        out.append(f"\n▶ <b>{it['topic'].upper()}</b> — {r.get('tong_quan', '?')}")
        out.append(f"✅ {r.get('phan_tram_tich_cuc', 0)}% | "
                   f"❌ {r.get('phan_tram_tieu_cuc', 0)}% | "
                   f"⚪ {r.get('phan_tram_trung_lap', 0)}%")
    if len(ok) >= 2:
        winner = max(ok, key=lambda it: it["result"].get("phan_tram_tich_cuc", 0))
        out.append(f"\n🏆 <b>Tích cực nhất:</b> {winner['topic'].upper()} "
                   f"({winner['result'].get('phan_tram_tich_cuc', 0)}%)")
    return "\n".join(out)
