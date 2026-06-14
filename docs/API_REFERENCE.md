# 📚 Tham chiếu API (hàm theo module)

Tài liệu liệt kê các hàm công khai của từng module, tham số, giá trị trả về và ví dụ dùng. Dùng để tra cứu khi mở rộng hoặc tích hợp.

---

## `engine.py` — Lõi điều phối

### `run_analysis(topic, limit=50, save_history=True, use_cache=True)`
Chạy toàn bộ pipeline cho **một** chủ đề.

| Tham số | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `topic` | str | — | Chủ đề/sản phẩm cần phân tích |
| `limit` | int | 50 | Số kết quả tối đa lấy từ mỗi nguồn |
| `save_history` | bool | True | Có lưu vào lịch sử không |
| `use_cache` | bool | True | Có dùng/ghi cache không |

**Trả về** `dict`:
```python
{
    "ok": bool,            # thành công hay không
    "error": str | None,   # thông báo lỗi nếu có
    "result": dict | None, # JSON sentiment (xem cấu trúc bên dưới)
    "source_count": int,   # số đoạn dữ liệu đã phân tích
    "cached": bool,        # kết quả lấy từ cache hay quét mới
}
```

**Ví dụ:**
```python
from engine import run_analysis

res = run_analysis("iPhone 15")
if res["ok"]:
    print(res["result"]["phan_tram_tich_cuc"])
```

### `run_comparison(topics, limit=50, save_history=True, use_cache=True)`
Phân tích **nhiều** chủ đề rồi gộp để so sánh.

- `topics`: chuỗi (`"iPhone vs Samsung"`) hoặc list (`["iPhone", "Samsung"]`).
- **Trả về** `dict`: `{ok, error, items}`, trong đó `items` là list các `{topic, ok, result, source_count, error}`.
- Cần ít nhất 2 chủ đề phân tích thành công, nếu không `ok=False`.

### `parse_topics(text)`
Tách chuỗi thành danh sách chủ đề. Hỗ trợ phân tách: `vs`, `versus`, `với`, dấu phẩy.
```python
parse_topics("iPhone vs Samsung")   # -> ["iPhone", "Samsung"]
parse_topics("A, B, C")              # -> ["A", "B", "C"]
```

### `clear_cache()`
Xóa toàn bộ cache trong bộ nhớ. Hữu ích cho test hoặc khi muốn ép quét mới.

### Hằng số
- `CACHE_TTL` (int, mặc định `600`) — thời gian sống của cache, tính bằng giây.

---

## `scraper.py` — Cào dữ liệu

### `fetch_market_data(query, limit=50)`
Hàm tổng hợp — gọi tất cả nguồn, khử trùng lặp, trả về list các đoạn text.

### `fetch_hackernews(query, limit=50)`
Cào tiêu đề story + bình luận từ Hacker News (Algolia API). Luôn bật.

### `fetch_google_news(query, limit=50, lang="en", country="US")`
Cào tiêu đề + mô tả tin từ Google News RSS. Gọi 2 lần (EN + VI) trong `fetch_market_data`.

### `fetch_youtube_comments(query, limit=50)`
Cào bình luận video YouTube. **Chỉ chạy nếu có `YOUTUBE_API_KEY`**, nếu không trả `[]`.

### `fetch_reddit(query, limit=50)`
Cào bài đăng Reddit qua OAuth. **Chỉ chạy nếu có `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET`**, nếu không trả `[]`.

### `_clean(text)` *(nội bộ)*
Bỏ thẻ HTML, giải mã ký tự đặc biệt, gộp khoảng trắng. Trả `""` nếu input rỗng/None.

---

## `analyzer.py` — Phân tích AI

### `analyze_sentiment(topic, text_data_list)`
Gửi dữ liệu cho Gemini, trả về JSON sentiment.

- **Trả về** `dict` theo cấu trúc chuẩn (xem dưới), hoặc `{"error": ...}` nếu không có dữ liệu, hoặc `None` nếu lỗi không hồi phục được.
- Tự cắt dữ liệu xuống 30.000 ký tự nếu vượt.
- Retry tối đa 3 lần khi gặp lỗi 503/429.

### Cấu trúc JSON kết quả
```python
{
    "tong_quan": str,            # "Tích Cực" / "Tiêu Cực" / "Trung Lập" / "Trái Chiều"
    "phan_tram_tich_cuc": int,   # 0-100
    "phan_tram_tieu_cuc": int,   # 0-100
    "phan_tram_trung_lap": int,  # 0-100 (tổng 3 cái = 100)
    "top_3_khen": list[str],     # 3 điểm được khen
    "top_3_che": list[str],      # 3 điểm bị chê
    "ket_luan_ngan": str,        # câu chốt 1-2 dòng
}
```

---

## `reporter.py` — Định dạng & xuất báo cáo

| Hàm | Mô tả |
|---|---|
| `format_text(topic, result)` | Báo cáo text thuần (cho terminal) |
| `format_markdown(topic, result)` | Báo cáo Markdown |
| `format_telegram(topic, result)` | Báo cáo HTML gọn cho Telegram |
| `format_comparison_text(items)` | Báo cáo so sánh dạng text |
| `format_comparison_telegram(items)` | Báo cáo so sánh dạng HTML Telegram |
| `save_report(topic, result, fmt="md")` | Lưu file (`fmt="md"` hoặc `"json"`), trả đường dẫn |

---

## `charts.py` — Biểu đồ

| Hàm | Mô tả | Trả về |
|---|---|---|
| `make_pie_chart(topic, result)` | Biểu đồ tròn tỷ lệ sentiment | đường dẫn PNG |
| `make_trend_chart(topic, records)` | Biểu đồ đường xu hướng (cần ≥2 bản ghi) | đường dẫn PNG hoặc `None` |
| `make_comparison_chart(items)` | Biểu đồ cột nhóm so sánh (cần ≥2 chủ đề) | đường dẫn PNG hoặc `None` |

---

## `history.py` — Lịch sử

| Hàm | Mô tả |
|---|---|
| `save_record(topic, result, source_count=0)` | Lưu một bản ghi kèm timestamp |
| `load_all()` | Đọc toàn bộ lịch sử (list, rỗng nếu chưa có / file hỏng) |
| `get_history_for_topic(topic)` | Lấy bản ghi của một chủ đề (không phân biệt hoa thường), sắp theo thời gian |
| `list_topics()` | Trả dict `{topic: số_lần}` |
