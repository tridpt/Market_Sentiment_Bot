"""Vẽ biểu đồ trực quan cho báo cáo sentiment bằng matplotlib (backend Agg, không cần GUI)."""
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # backend không cần màn hình, an toàn cho bot/server
import matplotlib.pyplot as plt
from matplotlib import font_manager

CHARTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "charts")


def _ensure_dir():
    os.makedirs(CHARTS_DIR, exist_ok=True)


def _slug(text):
    import re
    s = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    return re.sub(r"\s+", "_", s) or "chart"


def make_pie_chart(topic, result):
    """Vẽ biểu đồ tròn tỷ lệ tích cực/tiêu cực/trung lập. Trả về đường dẫn ảnh PNG."""
    _ensure_dir()
    tc = result.get("phan_tram_tich_cuc", 0)
    tieu = result.get("phan_tram_tieu_cuc", 0)
    tl = result.get("phan_tram_trung_lap", 0)

    labels = ["Tích cực", "Tiêu cực", "Trung lập"]
    sizes = [tc, tieu, tl]
    colors = ["#2ecc71", "#e74c3c", "#95a5a6"]

    # Lọc bỏ phần 0% để biểu đồ gọn
    filtered = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
    if not filtered:
        filtered = [("Không có dữ liệu", 1, "#bdc3c7")]
    labels, sizes, colors = zip(*filtered)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%",
           startangle=90, textprops={"fontsize": 12},
           wedgeprops={"edgecolor": "white", "linewidth": 2})
    ax.set_title(f"Tỷ lệ dư luận: {topic}", fontsize=14, fontweight="bold")
    ax.axis("equal")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CHARTS_DIR, f"pie_{_slug(topic)}_{ts}.png")
    fig.savefig(path, bbox_inches="tight", dpi=110)
    plt.close(fig)
    return path


def make_trend_chart(topic, records):
    """
    Vẽ biểu đồ đường biến động sentiment theo thời gian từ danh sách bản ghi lịch sử.
    records: list dict có 'timestamp', 'phan_tram_tich_cuc', 'phan_tram_tieu_cuc', 'phan_tram_trung_lap'.
    Trả về đường dẫn ảnh PNG, hoặc None nếu chưa đủ dữ liệu (cần >= 2 mốc).
    """
    if len(records) < 2:
        return None
    _ensure_dir()

    xs = list(range(len(records)))
    times = [r.get("timestamp", "")[5:16].replace("T", " ") for r in records]
    pos = [r.get("phan_tram_tich_cuc", 0) for r in records]
    neg = [r.get("phan_tram_tieu_cuc", 0) for r in records]
    neu = [r.get("phan_tram_trung_lap", 0) for r in records]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(xs, pos, marker="o", color="#2ecc71", label="Tích cực", linewidth=2)
    ax.plot(xs, neg, marker="o", color="#e74c3c", label="Tiêu cực", linewidth=2)
    ax.plot(xs, neu, marker="o", color="#95a5a6", label="Trung lập", linewidth=2)
    ax.set_xticks(xs)
    ax.set_xticklabels(times, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Tỷ lệ (%)")
    ax.set_ylim(0, 100)
    ax.set_title(f"Xu hướng cảm xúc theo thời gian: {topic}", fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CHARTS_DIR, f"trend_{_slug(topic)}_{ts}.png")
    fig.savefig(path, bbox_inches="tight", dpi=110)
    plt.close(fig)
    return path


def make_comparison_chart(items):
    """
    Vẽ biểu đồ cột nhóm so sánh nhiều chủ đề.
    items: list dict {topic, result} (chỉ các item phân tích thành công).
    Trả về đường dẫn ảnh PNG, hoặc None nếu < 2 chủ đề.
    """
    import numpy as np

    ok = [it for it in items if it.get("result")]
    if len(ok) < 2:
        return None
    _ensure_dir()

    topics = [it["topic"] for it in ok]
    pos = [it["result"].get("phan_tram_tich_cuc", 0) for it in ok]
    neg = [it["result"].get("phan_tram_tieu_cuc", 0) for it in ok]
    neu = [it["result"].get("phan_tram_trung_lap", 0) for it in ok]

    x = np.arange(len(topics))
    width = 0.25

    fig, ax = plt.subplots(figsize=(max(7, len(topics) * 2.2), 5.5))
    b1 = ax.bar(x - width, pos, width, label="Tích cực", color="#2ecc71")
    b2 = ax.bar(x, neg, width, label="Tiêu cực", color="#e74c3c")
    b3 = ax.bar(x + width, neu, width, label="Trung lập", color="#95a5a6")

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{int(h)}%", xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(topics, fontsize=11)
    ax.set_ylabel("Tỷ lệ (%)")
    ax.set_ylim(0, 100)
    ax.set_title("So sánh cảm xúc thị trường", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _slug("_".join(topics)[:40])
    path = os.path.join(CHARTS_DIR, f"compare_{slug}_{ts}.png")
    fig.savefig(path, bbox_inches="tight", dpi=110)
    plt.close(fig)
    return path
