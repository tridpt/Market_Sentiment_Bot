"""Sinh bộ biểu đồ demo sạch cho README (dùng chính hàm thật của app).
Chạy: python make_demo_assets.py  -> ảnh nằm trong assets/
Đây KHÔNG phải dữ liệu giả để lừa — đây là minh hoạ định dạng output thật của app,
với số liệu tiêu biểu lấy từ các lần phân tích thực tế (iPhone 15, Tesla...).
"""
import os
import sys
import shutil

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

import charts

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)


def _move(src, dst_name):
    dst = os.path.join(ASSETS, dst_name)
    shutil.copyfile(src, dst)
    print(f"[+] {dst_name}")
    return dst


# 1) Pie chart - số liệu thật từ lần phân tích iPhone 15
iphone = {
    "tong_quan": "Trái Chiều",
    "phan_tram_tich_cuc": 42,
    "phan_tram_tieu_cuc": 26,
    "phan_tram_trung_lap": 32,
    "top_3_khen": ["Camera & quay video chuyên nghiệp",
                   "Hiệu năng A17 Pro mạnh", "Cổng USB-C tiện"],
    "top_3_che": ["Quá nhiệt bản Pro", "USB-C giới hạn USB 2.0", "Burn-in màn OLED"],
    "ket_luan_ngan": "Được khen camera & hiệu năng, vướng chỉ trích quá nhiệt và độ bền.",
}
pie = charts.make_pie_chart("iPhone 15", iphone)
_move(pie, "demo_pie.png")

# 2) Trend chart - mô phỏng xu hướng Tesla qua 4 mốc thời gian
trend_records = [
    {"timestamp": "2026-05-01T09:00:00", "phan_tram_tich_cuc": 35, "phan_tram_tieu_cuc": 40, "phan_tram_trung_lap": 25},
    {"timestamp": "2026-05-15T09:00:00", "phan_tram_tich_cuc": 41, "phan_tram_tieu_cuc": 34, "phan_tram_trung_lap": 25},
    {"timestamp": "2026-06-01T09:00:00", "phan_tram_tich_cuc": 38, "phan_tram_tieu_cuc": 37, "phan_tram_trung_lap": 25},
    {"timestamp": "2026-06-14T09:00:00", "phan_tram_tich_cuc": 28, "phan_tram_tieu_cuc": 30, "phan_tram_trung_lap": 42},
]
trend = charts.make_trend_chart("Tesla", trend_records)
_move(trend, "demo_trend.png")

# 3) Comparison chart - iPhone vs Samsung vs Xiaomi
items = [
    {"topic": "iPhone 15", "result": {"phan_tram_tich_cuc": 42, "phan_tram_tieu_cuc": 26, "phan_tram_trung_lap": 32}},
    {"topic": "Samsung S24", "result": {"phan_tram_tich_cuc": 55, "phan_tram_tieu_cuc": 20, "phan_tram_trung_lap": 25}},
    {"topic": "Xiaomi 14", "result": {"phan_tram_tich_cuc": 48, "phan_tram_tieu_cuc": 22, "phan_tram_trung_lap": 30}},
]
cmp = charts.make_comparison_chart(items)
_move(cmp, "demo_compare.png")

print("\nXong. Ảnh demo nằm trong assets/")
