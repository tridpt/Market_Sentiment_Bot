# 📖 Hướng dẫn sử dụng chi tiết

Tài liệu này hướng dẫn dùng đầy đủ cả 3 giao diện và xử lý các tình huống thường gặp.

---

## 1. Chuẩn bị

Trước khi dùng bất kỳ giao diện nào, đảm bảo đã:

1. Cài dependencies: `pip install -r requirements.txt`
2. Tạo file `.env` (copy từ `.env.example`) và điền tối thiểu `GEMINI_API_KEY`.

Xem [SETUP](../README.md#-cài-đặt) trong README nếu chưa làm.

---

## 2. CLI (`main.py`)

Cách nhanh nhất để chạy thử.

```bash
python main.py
```

Nhập chủ đề khi được hỏi:

```
Nhập sản phẩm/chủ đề bạn muốn soi: iPhone 15
```

**Phân tích đơn:** gõ một tên → nhận báo cáo + tự lưu file MD/JSON + biểu đồ tròn (và biểu đồ xu hướng nếu chủ đề đã quét ≥2 lần).

**So sánh:** gõ nhiều tên cách nhau bằng `vs` hoặc dấu phẩy:
```
iPhone 15 vs Samsung S24
```
→ báo cáo từng máy + biểu đồ cột so sánh.

Các file kết quả nằm trong `reports/` (báo cáo) và `reports/charts/` (ảnh).

---

## 3. Telegram Bot (`bot.py`)

Cần `TELEGRAM_BOT_TOKEN` trong `.env`.

```bash
python bot.py
```

Bot chạy nền liên tục (Ctrl+C để dừng). Mở Telegram, tìm bot của bạn và dùng:

| Lệnh / hành động | Kết quả |
|---|---|
| `/start` | Lời chào + hướng dẫn |
| Nhắn `iPhone 15` | Phân tích chủ đề đó |
| Nhắn `iPhone vs Samsung` | Tự nhận diện → so sánh |
| `/compare iPhone vs Samsung` | So sánh (cú pháp tường minh) |
| `/trend iPhone` | Biểu đồ xu hướng (cần ≥2 lần phân tích) |
| `/history` | Liệt kê các chủ đề đã phân tích |

**Giới hạn người dùng:** nếu đặt `ALLOWED_USER_ID` trong `.env`, chỉ user đó dùng được bot. Để trống = ai cũng dùng được.

> Cách lấy user ID của bạn: nhắn cho [@userinfobot](https://t.me/userinfobot) trên Telegram.

---

## 4. Web UI (`webapp.py`)

```bash
python webapp.py
```

Mở trình duyệt: http://127.0.0.1:5000

- Gõ chủ đề vào ô tìm kiếm → bấm **Phân tích**.
- Gõ `iPhone vs Samsung` để vào chế độ so sánh.
- Báo cáo hiển thị kèm thanh tỷ lệ và biểu đồ.

> Trang sẽ "loading" 15–30 giây mỗi lần phân tích vì phải cào nhiều nguồn rồi gọi Gemini. Đây là bình thường.

---

## 5. Bật thêm nguồn dữ liệu (tùy chọn)

Mặc định bot dùng Hacker News + Google News. Để thêm nguồn, điền key vào `.env`:

**YouTube** (bình luận video):
```
YOUTUBE_API_KEY="..."
```
Lấy tại [Google Cloud Console](https://console.cloud.google.com/apis/credentials), nhớ bật "YouTube Data API v3".

**Reddit** (bài đăng, qua OAuth chính thức):
```
REDDIT_CLIENT_ID="..."
REDDIT_CLIENT_SECRET="..."
REDDIT_USER_AGENT="python:sentiment_bot:v1.0 (by /u/tên_bạn)"
```
Tạo app dạng **script** tại [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).

Không điền cũng không sao — app tự bỏ qua nguồn chưa cấu hình.

---

## 6. Xử lý sự cố

| Triệu chứng | Nguyên nhân & cách xử lý |
|---|---|
| `Chưa tìm thấy GEMINI_API_KEY` | Chưa tạo `.env` hoặc thiếu key. Copy từ `.env.example` và điền. |
| `Không cào được dữ liệu nào` | Từ khóa quá hiếm, hoặc mạng lỗi. Thử từ khóa phổ biến hơn. |
| `AI phân tích thất bại` | Gemini quá tải (đã retry 3 lần). Chờ chút rồi thử lại. |
| Bot trả `⛔ Bạn không có quyền` | `ALLOWED_USER_ID` không khớp ID của bạn. Sửa lại trong `.env`. |
| Emoji lỗi font khi pipe trên Windows | Đã xử lý bằng ép UTF-8; chữ méo trên console không ảnh hưởng file lưu ra. |
| Kết quả giống hệt lần trước | Đang lấy từ cache (trong 10 phút). Đổi `CACHE_TTL` hoặc gọi `clear_cache()`. |

---

## 7. Mẹo

- **Tiết kiệm quota Gemini:** cache giữ kết quả 10 phút. Quét lại cùng chủ đề trong khoảng này không tốn thêm lần gọi API.
- **Đo xu hướng:** quét cùng một chủ đề định kỳ (vd mỗi tuần) để `/trend` vẽ được đường biến động.
- **So sánh nhiều hơn 2:** `iPhone vs Samsung vs Xiaomi` vẫn chạy được — biểu đồ cột tự giãn.
