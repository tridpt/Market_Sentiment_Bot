"""Chụp ảnh giao diện Web UI bằng Playwright, dùng DỮ LIỆU MẪU (không gọi Gemini/quota).

Cách chạy: venv\\Scripts\\python.exe make_web_screenshot.py
Ảnh lưu vào assets/.
"""
import os
import sys
import time
import threading

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

import webapp
import charts

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)

# ---- Dữ liệu mẫu (không gọi API) ----
SAMPLE = {
    "tong_quan": "Trái Chiều",
    "phan_tram_tich_cuc": 42,
    "phan_tram_tieu_cuc": 26,
    "phan_tram_trung_lap": 32,
    "top_3_khen": [
        "Camera và khả năng quay video chuyên nghiệp",
        "Hiệu năng mạnh mẽ (chip A17 Pro), chơi game AAA mượt",
        "Cổng USB-C, kết nối đa dạng",
    ],
    "top_3_che": [
        "Vấn đề quá nhiệt trên bản Pro / Pro Max",
        "USB-C giới hạn tốc độ USB 2.0, khó sửa chữa",
        "Lỗi màn hình OLED (burn-in)",
    ],
    "ket_luan_ngan": "iPhone 15 được khen về camera & hiệu năng, nhưng vướng chỉ trích về quá nhiệt và độ bền.",
}

SAMPLE2 = {
    "tong_quan": "Tích Cực",
    "phan_tram_tich_cuc": 58,
    "phan_tram_tieu_cuc": 18,
    "phan_tram_trung_lap": 24,
    "top_3_khen": ["Màn hình AMOLED đẹp", "Giá hợp lý so với cấu hình", "Pin trâu"],
    "top_3_che": ["Phần mềm còn quảng cáo", "Camera đêm chưa tốt", "Cập nhật chậm"],
    "ket_luan_ngan": "Samsung được đánh giá tích cực nhờ màn hình và giá trị đồng tiền.",
}


def fake_run_analysis(topic, limit=50, save_history=True, use_cache=True):
    return {"ok": True, "error": None, "result": SAMPLE, "source_count": 100, "cached": False}


def fake_run_comparison(topics, limit=50, save_history=True, use_cache=True):
    return {"ok": True, "error": None, "items": [
        {"topic": topics[0], "ok": True, "result": SAMPLE, "source_count": 100, "error": None},
        {"topic": topics[1] if len(topics) > 1 else "Samsung", "ok": True,
         "result": SAMPLE2, "source_count": 95, "error": None},
    ]}


# Mock engine trong namespace webapp + charts (dùng chart demo có sẵn để khỏi vẽ lại)
webapp.run_analysis = fake_run_analysis
webapp.run_comparison = fake_run_comparison


def _start_server():
    webapp.app.run(host="127.0.0.1", port=5055, debug=False, use_reloader=False)


def main():
    t = threading.Thread(target=_start_server, daemon=True)
    t.start()
    time.sleep(2.5)  # chờ server lên

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900},
                                device_scale_factor=2)

        # 1) Trang phân tích đơn
        page.goto("http://127.0.0.1:5055/?topic=iPhone%2015", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(ASSETS, "web_analysis.png"), full_page=True)
        print("[+] web_analysis.png")

        # 2) Trang so sánh
        page.goto("http://127.0.0.1:5055/?topic=iPhone%20vs%20Samsung", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(ASSETS, "web_compare.png"), full_page=True)
        print("[+] web_compare.png")

        browser.close()

    print("Xong. Ảnh web nằm trong assets/")


if __name__ == "__main__":
    main()
