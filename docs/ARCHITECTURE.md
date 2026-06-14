# 🏗️ Kiến trúc hệ thống

Tài liệu này mô tả cách Market Sentiment Bot được tổ chức, luồng dữ liệu chạy qua hệ thống, và lý do đằng sau các quyết định thiết kế chính.

## Tổng quan

Hệ thống được thiết kế theo nguyên tắc **một lõi xử lý, nhiều giao diện**. Toàn bộ logic nghiệp vụ (cào dữ liệu → phân tích → lưu trữ) nằm trong các module dùng chung, còn CLI / Telegram bot / Web UI chỉ là các lớp mỏng gọi vào lõi đó.

Lợi ích: thêm một giao diện mới (vd Discord bot) chỉ cần gọi `engine.run_analysis()` — không phải viết lại logic.

```
┌──────────┐   ┌──────────┐   ┌──────────┐
│ main.py  │   │  bot.py  │   │webapp.py │   ← 3 giao diện (lớp mỏng)
│  (CLI)   │   │(Telegram)│   │ (Flask)  │
└────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │
     └──────────────┼──────────────┘
                    ▼
            ┌───────────────┐
            │   engine.py   │              ← Lõi điều phối
            │ pipeline+cache│
            └───┬───────┬───┘
       ┌────────┘       └────────┐
       ▼                         ▼
┌─────────────┐          ┌──────────────┐
│ scraper.py  │          │ analyzer.py  │   ← Lấy dữ liệu & phân tích AI
│ (đa nguồn)  │          │  (Gemini)    │
└─────────────┘          └──────────────┘
       │                         │
       └───────────┬─────────────┘
                   ▼
   ┌───────────┬───────────┬───────────┐
   ▼           ▼           ▼           ▼
reporter.py  charts.py  history.py   (output)   ← Trình bày & lưu trữ
```

## Luồng dữ liệu (một lần phân tích)

1. **Người dùng nhập chủ đề** qua một trong 3 giao diện.
2. Giao diện gọi `engine.run_analysis(topic)`.
3. **Engine kiểm tra cache** — nếu chủ đề đã quét trong vòng `CACHE_TTL` (mặc định 600s) thì trả kết quả cũ, dừng tại đây.
4. **`scraper.fetch_market_data()`** cào song song từ các nguồn (Hacker News, Google News EN/VI, tùy chọn YouTube/Reddit), dọn HTML, khử trùng lặp.
5. **`analyzer.analyze_sentiment()`** gom dữ liệu thành một prompt, gửi cho Gemini, nhận về JSON có cấu trúc. Có retry khi server quá tải.
6. **`history.save_record()`** lưu kết quả kèm timestamp vào `data/history.json`.
7. Engine **lưu kết quả vào cache** rồi trả về cho giao diện.
8. Giao diện dùng **`reporter`** (định dạng văn bản) và **`charts`** (vẽ biểu đồ) để trình bày.

## Vai trò từng module

| Module | Trách nhiệm | Phụ thuộc |
|---|---|---|
| `scraper.py` | Cào dữ liệu thô từ nhiều nguồn, dọn rác, khử trùng lặp | `requests` |
| `analyzer.py` | Biến dữ liệu thô thành JSON sentiment qua Gemini | `google-genai` |
| `engine.py` | Điều phối pipeline, cache, so sánh nhiều chủ đề | `scraper`, `analyzer`, `history` |
| `reporter.py` | Định dạng kết quả ra text / Markdown / JSON / HTML Telegram | — |
| `charts.py` | Vẽ biểu đồ tròn / đường / cột (matplotlib) | `matplotlib` |
| `history.py` | Lưu & truy xuất lịch sử phân tích (JSON file) | — |
| `bot.py` | Giao diện Telegram (async) | `python-telegram-bot`, `engine` |
| `webapp.py` | Giao diện Web (Flask) | `flask`, `engine` |
| `main.py` | Giao diện CLI | `engine` |

## Quyết định thiết kế

### Vì sao tách `engine.py` khỏi giao diện?
Tránh lặp logic. Trước khi có engine, mỗi giao diện sẽ phải tự gọi scraper → analyzer → history theo đúng thứ tự và tự xử lý lỗi. Gom vào một chỗ giúp sửa logic một lần, áp dụng mọi nơi, và dễ viết test (chỉ cần test `engine`).

### Vì sao cache trong bộ nhớ (in-memory) thay vì database?
Đơn giản và đủ dùng. Cache chỉ cần sống trong một phiên chạy để tránh gọi lại Gemini cho cùng chủ đề trong thời gian ngắn. Mất cache khi restart là chấp nhận được — không đáng để thêm phụ thuộc database.

### Vì sao nguồn dữ liệu phụ (YouTube/Reddit) là tùy chọn?
Để hạ rào cản dùng thử. Người dùng chỉ cần `GEMINI_API_KEY` là chạy được ngay với Hacker News + Google News. Nếu thiếu credentials của nguồn phụ, các hàm tương ứng trả về list rỗng và bỏ qua êm thay vì làm vỡ pipeline.

### Vì sao matplotlib dùng backend `Agg`?
`Agg` không cần màn hình (headless), an toàn khi chạy trong bot/server không có GUI. Biểu đồ được render thẳng ra file PNG.

## Lưu trữ dữ liệu

- `data/history.json` — toàn bộ lịch sử phân tích (mỗi bản ghi gồm topic, timestamp, tỷ lệ %, full result).
- `reports/*.md`, `reports/*.json` — báo cáo xuất ra theo từng lần chạy CLI.
- `reports/charts/*.png` — ảnh biểu đồ.

Cả ba thư mục đều được `.gitignore` loại trừ (dữ liệu sinh ra lúc chạy, không commit).

## Xử lý lỗi

- **Scraper**: mỗi nguồn bọc trong try/except riêng — một nguồn lỗi không làm hỏng các nguồn còn lại.
- **Analyzer**: retry 3 lần khi gặp lỗi 503/429 (server quá tải), chờ 5s giữa các lần.
- **Engine**: lỗi khi lưu lịch sử được nuốt (không làm hỏng kết quả phân tích đã có).
- **Charts/Reporter trong giao diện**: bọc try/except để lỗi vẽ biểu đồ không chặn việc trả báo cáo text.

## Điểm cần biết

- Prompt trong `analyzer.py` hiện vẫn nhắc đến "Reddit" như nguồn ví dụ (di sản từ phiên bản đầu chỉ cào Reddit). Điều này không ảnh hưởng kết quả nhưng có thể cập nhật cho khớp với nguồn đa dạng hiện tại.
- Giới hạn prompt 30.000 ký tự là để cân bằng giữa độ phủ dữ liệu và chi phí/tốc độ. Gemini 2.5 Flash chịu được context lớn hơn nhiều nếu cần nâng.
