<div align="center">

# 📊 Market Sentiment Bot

**Đo "nhiệt" dư luận của bất kỳ sản phẩm/chủ đề nào — bằng AI, trong vài giây.**

Nhập một cái tên (vd *iPhone 15*, *VinFast*), bot tự cào tin tức + diễn đàn từ nhiều nguồn,
rồi nhờ **Google Gemini** tổng hợp xem cộng đồng đang khen gì, chê gì, thái độ chung ra sao.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)
![Telegram](https://img.shields.io/badge/Bot-Telegram-26A5E4?logo=telegram&logoColor=white)
![Flask](https://img.shields.io/badge/Web-Flask-000000?logo=flask&logoColor=white)
![Tests](https://img.shields.io/badge/tests-44%20passing-2ecc71)
![License](https://img.shields.io/badge/license-MIT-blue)

</div>

---

## 🎯 Bài toán

Trước khi mua một món đồ, đầu tư vào một công ty, hay chọn giữa hai sản phẩm — ai cũng đi đọc
review, lượn diễn đàn, xem tin tức. Việc đó tốn hàng giờ và rất khó tổng hợp lại thành một
kết luận rõ ràng.

**Market Sentiment Bot** làm hộ bạn việc đó: gom hàng trăm ý kiến rải rác trên mạng rồi nén
lại thành một báo cáo gọn — tỷ lệ tích cực/tiêu cực, top điểm khen/chê, và một câu chốt hạ.

## ✨ Tính năng

| | |
|---|---|
| 🤖 **Telegram Bot** | Nhắn tên sản phẩm → nhận báo cáo + biểu đồ ngay trong chat |
| 🌐 **Web UI** | Giao diện Flask gọn gàng, xem báo cáo trực quan trên trình duyệt |
| 💻 **CLI** | Chạy nhanh từ terminal, tự xuất file + biểu đồ |
| ⚖️ **So sánh sản phẩm** | Nhập `iPhone vs Samsung` → biểu đồ cột cạnh nhau + ai được khen nhất |
| 📈 **Biểu đồ** | Tròn (tỷ lệ sentiment), đường (xu hướng theo thời gian), cột (so sánh) |
| 🕒 **Theo dõi xu hướng** | Lưu lịch sử để xem dư luận thay đổi qua thời gian |
| 📄 **Xuất báo cáo** | Markdown + JSON có timestamp, lưu lại để đối chiếu |
| ⚡ **Cache thông minh** | Quét lại cùng chủ đề trong 10 phút trả kết quả cũ — tiết kiệm quota Gemini |
| 🌍 **Đa nguồn** | Hacker News + Google News (Anh & Việt); tùy chọn thêm YouTube + Reddit |

## 🔧 Cách hoạt động

```
   Bạn nhập chủ đề
        │
        ▼
┌─────────────────┐     Hacker News · Google News (EN/VI)
│   scraper.py    │ ◀── (+ YouTube · Reddit nếu có key)
│  cào + dọn rác  │     khử trùng lặp, lọc bài quá ngắn
└────────┬────────┘
         │  hàng trăm đoạn ý kiến
         ▼
┌─────────────────┐
│   analyzer.py   │ ──▶  Google Gemini 2.5 Flash
│  prompt + JSON  │      (trả về JSON có cấu trúc, có retry khi quá tải)
└────────┬────────┘
         │  {tỷ lệ %, top khen, top chê, kết luận}
         ▼
┌─────────────────┐
│    engine.py    │  cache · lưu lịch sử
└────────┬────────┘
         │
         ▼
   📊 Báo cáo + biểu đồ
   (CLI · Telegram · Web)
```

## 🖼️ Ví dụ kết quả

```
============================================================
📊 BẢNG BÁO CÁO CẢM XÚC THỊ TRƯỜNG: IPHONE 15 📊
============================================================
>> THÁI ĐỘ TỔNG QUAN: TRÁI CHIỀU
>> TỶ LỆ DƯ LUẬN: Tích cực (42%) | Tiêu cực (26%) | Trung lập (32%)

✅ TOP 3 ĐIỂM ĐƯỢC KHEN:
  1. Camera và khả năng quay video chuyên nghiệp
  2. Hiệu năng mạnh mẽ (chip A17 Pro), chơi game AAA mượt
  3. Cổng USB-C, kết nối đa dạng

❌ TOP 3 ĐIỂM BỊ CHÊ/BỨC XÚC:
  1. Vấn đề quá nhiệt trên bản Pro / Pro Max
  2. USB-C giới hạn tốc độ USB 2.0, khó sửa chữa
  3. Lỗi màn hình OLED (burn-in)

💡 KẾT LUẬN: iPhone 15 được khen về camera & hiệu năng,
   nhưng vướng chỉ trích về quá nhiệt và độ bền.
============================================================
```

> Chế độ so sánh (`iPhone vs Samsung`) sẽ vẽ biểu đồ cột nhóm và chỉ ra sản phẩm có dư luận tích cực nhất.

## 🛠️ Tech Stack

- **Python 3.13**
- **Google Gemini 2.5 Flash** (`google-genai`) — phân tích ngôn ngữ tự nhiên, trả JSON có cấu trúc
- **python-telegram-bot 22** (async) — giao diện chat
- **Flask 3** — Web UI
- **matplotlib** — biểu đồ tròn / đường / cột
- **requests** — cào dữ liệu (REST + RSS)
- **pytest** — 44 unit test (mock, không gọi API thật)

## 🚀 Cài đặt

```bash
git clone https://github.com/tridpt/Market_Sentiment_Bot.git
cd Market_Sentiment_Bot

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

Tạo file cấu hình từ mẫu rồi điền key:

```bash
copy .env.example .env         # Windows  (Linux/macOS: cp)
```

| Biến | Bắt buộc | Lấy ở đâu |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | https://aistudio.google.com/apikey |
| `TELEGRAM_BOT_TOKEN` | chỉ khi chạy bot | [@BotFather](https://t.me/BotFather) |
| `ALLOWED_USER_ID` | tùy chọn | Giới hạn chỉ một user được dùng bot |
| `YOUTUBE_API_KEY` | tùy chọn | Bật nguồn bình luận YouTube |
| `REDDIT_CLIENT_ID` / `SECRET` | tùy chọn | Bật nguồn Reddit (OAuth) |

## 📖 Cách dùng

**Telegram bot**
```bash
python bot.py
```
Nhắn tên sản phẩm (vd `iPhone 15`). Lệnh: `/start`, `/history`, `/trend <chủ đề>`, `/compare iPhone vs Samsung`.
Mẹo: nhắn thẳng `iPhone vs Samsung` là bot tự hiểu sang chế độ so sánh.

**Web UI**
```bash
python webapp.py     # mở http://127.0.0.1:5000
```

**CLI**
```bash
python main.py
```

## 🧪 Kiểm thử

```bash
python -m pytest tests/ -v
```

44 test dùng **mock** nên không gọi API thật (không tốn quota, không cần mạng). Bao phủ:
định dạng báo cáo, lưu/đọc lịch sử, logic cache, parse & so sánh nhiều chủ đề, dọn dữ liệu,
và logic bỏ qua nguồn tùy chọn khi thiếu key.

## 📁 Cấu trúc dự án

```
Market_Sentiment_Bot/
├── scraper.py        # Cào dữ liệu đa nguồn + dọn rác
├── analyzer.py       # Gọi Gemini, trả JSON có cấu trúc
├── engine.py         # Lõi: pipeline + cache + so sánh
├── reporter.py       # Định dạng & xuất báo cáo (text/MD/JSON)
├── charts.py         # Biểu đồ pie / trend / compare
├── history.py        # Lưu & truy xuất lịch sử
├── bot.py            # Telegram bot (async)
├── webapp.py         # Web UI (Flask)
├── main.py           # CLI
├── tests/            # 44 unit test (pytest)
├── requirements.txt
└── .env.example
```

## 🗺️ Hướng phát triển

- [ ] Trích nguồn (đính link bài viết gốc trong báo cáo)
- [ ] Lọc theo khoảng thời gian (1 tuần / 1 tháng / 1 năm)
- [ ] Deploy 24/7 (Railway / Render) để bot luôn online
- [ ] Bot tự quét theo lịch và gửi báo cáo xu hướng định kỳ

## ⚠️ Lưu ý bảo mật

- **Không commit `.env`** — file này chứa token/API key thật và đã được `.gitignore` loại trừ.
- Web UI mặc định chỉ chạy `127.0.0.1` (máy bạn) và **chưa có xác thực** — đừng expose ra internet khi chưa thêm lớp bảo vệ.

## 📄 License

MIT — tự do dùng, sửa, chia sẻ.
