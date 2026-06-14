# 🤝 Hướng dẫn đóng góp & phát triển

Tài liệu cho người muốn sửa code hoặc mở rộng dự án.

---

## Thiết lập môi trường dev

```bash
git clone https://github.com/tridpt/Market_Sentiment_Bot.git
cd Market_Sentiment_Bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Tạo `.env` từ `.env.example` và điền `GEMINI_API_KEY` để chạy thử thật.
(Chạy test thì **không cần** key — test dùng mock.)

---

## Chạy test

```bash
python -m pytest tests/ -v
```

Mọi thay đổi code nên giữ test xanh. Quy ước test:

- **Không gọi API thật.** Dùng `monkeypatch` thay `fetch_market_data` / `analyze_sentiment`.
- **Không đụng dữ liệu thật.** Dùng `tmp_path` cho file, trỏ `REPORTS_DIR` / `HISTORY_FILE` về thư mục tạm.
- Mỗi test độc lập; với cache nhớ gọi `engine.clear_cache()` trong `setup_function`.

---

## Phong cách code

- Python theo PEP 8, thụt 4 dấu cách.
- Docstring tiếng Việt, mô tả "làm gì" hơn là "làm thế nào".
- Tên hàm/biến rõ nghĩa; ưu tiên đọc hiểu hơn là ngắn gọn.
- Mỗi module một trách nhiệm rõ ràng (xem [ARCHITECTURE](ARCHITECTURE.md)).

---

## Thêm một nguồn dữ liệu mới

Đây là loại mở rộng phổ biến nhất. Các bước:

1. Viết hàm `fetch_<tên_nguồn>(query, limit=50)` trong `scraper.py`.
   - Trả về `list[str]` — mỗi phần tử là một đoạn ý kiến đã dọn sạch (dùng `_clean`).
   - Lọc bỏ đoạn dưới 20 ký tự.
   - Bọc trong `try/except`, lỗi thì in cảnh báo và trả `[]` (không làm crash pipeline).
   - Nếu cần API key, đọc từ `os.getenv(...)`; thiếu key thì `return []` (bỏ qua êm).
2. Thêm lời gọi vào `fetch_market_data()`:
   ```python
   all_texts.extend(fetch_my_source(query, limit))
   ```
3. Thêm test trong `tests/test_scraper.py` (mock request, kiểm tra parse + skip khi thiếu key).
4. Cập nhật `.env.example` và README nếu nguồn cần cấu hình.

---

## Thêm một loại biểu đồ mới

1. Viết hàm trong `charts.py`, theo mẫu sẵn có:
   - Dùng backend `Agg` (đã set sẵn đầu file).
   - Lưu vào `CHARTS_DIR`, tên file có timestamp, trả về đường dẫn.
   - Luôn `plt.close(fig)` để tránh rò bộ nhớ.
2. Gọi từ `main.py` / `bot.py` / `webapp.py` tùy nơi cần hiển thị.

---

## Thay đổi cấu trúc JSON của AI

Nếu sửa prompt trong `analyzer.py` để đổi các khóa JSON, nhớ cập nhật đồng bộ:

- `reporter.py` — mọi hàm `format_*` đọc các khóa này.
- `charts.py` — đọc `phan_tram_*`.
- `history.py` — `save_record` lưu các khóa này.
- Các test có `SAMPLE` / `SAMPLE_RESULT`.

> Mẹo: các khóa hiện tại là `tong_quan`, `phan_tram_tich_cuc/tieu_cuc/trung_lap`, `top_3_khen`, `top_3_che`, `ket_luan_ngan`. Đổi một khóa = grep toàn repo để sửa hết.

---

## Quy trình commit

```bash
python -m pytest tests/      # đảm bảo xanh trước
git add .
git commit -m "loại: mô tả ngắn"   # vd: feat / fix / docs / test / refactor
git push
```

Đừng commit `.env`, `reports/`, `data/`, `venv/` — đã được `.gitignore` loại trừ.

---

## Ý tưởng mở rộng (roadmap)

- Trích nguồn: giữ URL bài viết kèm text, hiển thị link trong báo cáo.
- Lọc theo thời gian: thêm tham số `t` (week/month/year) cho Google News + Reddit.
- Deploy 24/7: Dockerfile + cấu hình Railway/Render, đọc env từ biến môi trường cloud.
- Lập lịch: dùng `JobQueue` của python-telegram-bot để tự quét định kỳ.
