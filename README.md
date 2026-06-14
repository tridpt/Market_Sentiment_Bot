# 📊 Market Sentiment Bot

Công cụ phân tích tâm lý thị trường (market sentiment) dùng AI. Nhập tên một sản phẩm/chủ đề, bot sẽ cào tin tức + diễn đàn rồi nhờ **Google Gemini** tổng hợp xem cộng đồng đang khen/chê gì, thái độ chung tích cực hay tiêu cực.

## ✨ Tính năng

- 🤖 **Telegram Bot** – nhắn tên sản phẩm, nhận báo cáo + biểu đồ ngay trong chat
- 🌐 **Web UI** (Flask) – nhập từ khóa, xem báo cáo trên trình duyệt
- 💻 **CLI** – chạy nhanh từ terminal
- 📄 **Xuất báo cáo** ra Markdown + JSON có timestamp
- 📈 **Biểu đồ** tròn (tỷ lệ sentiment) + đường (xu hướng theo thời gian)
- 🕒 **Theo dõi xu hướng** – lưu lịch sử để so sánh dư luận qua thời gian
- 🌍 **Đa nguồn** – Hacker News + Google News (tiếng Anh & tiếng Việt)

## 🏗️ Kiến trúc

| File | Vai trò |
|---|---|
| `scraper.py` | Cào dữ liệu từ Hacker News + Google News |
| `analyzer.py` | Gửi dữ liệu cho Gemini phân tích, trả JSON |
| `engine.py` | Lõi chung: cào → phân tích → lưu lịch sử |
| `reporter.py` | Định dạng & xuất báo cáo (text/Markdown/JSON) |
| `charts.py` | Vẽ biểu đồ pie + trend (matplotlib) |
| `history.py` | Lưu/đọc lịch sử phân tích |
| `bot.py` | Telegram bot |
| `webapp.py` | Web UI (Flask) |
| `main.py` | CLI |

## 🚀 Cài đặt

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

Sao chép `.env.example` thành `.env` và điền các giá trị:

```bash
copy .env.example .env       # Windows
```

- `GEMINI_API_KEY` – lấy tại https://aistudio.google.com/apikey
- `TELEGRAM_BOT_TOKEN` – tạo bot qua [@BotFather](https://t.me/BotFather)
- `ALLOWED_USER_ID` – (tùy chọn) chỉ cho phép một user dùng bot

## 📖 Cách dùng

**Telegram bot:**
```bash
python bot.py
```
Nhắn cho bot tên sản phẩm (vd `iPhone 15`). Lệnh: `/start`, `/history`, `/trend <chủ đề>`.

**Web UI:**
```bash
python webapp.py
```
Mở http://127.0.0.1:5000

**CLI:**
```bash
python main.py
```

## ⚠️ Lưu ý bảo mật

- Không commit file `.env` (đã được `.gitignore` loại trừ).
- Web UI mặc định chạy `127.0.0.1` và chưa có xác thực — đừng expose ra internet khi chưa thêm lớp bảo vệ.
