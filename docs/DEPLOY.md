# 🚀 Triển khai 24/7

Hướng dẫn đưa Market Sentiment Bot lên chạy liên tục. Có 3 tiến trình có thể chạy độc lập:

| Tiến trình | Lệnh | Vai trò |
|---|---|---|
| Web UI | `gunicorn ... webapp:app` | Giao diện web (mặc định của Docker image) |
| Telegram bot | `python bot.py` | Bot chat |
| Scheduler | `python scheduler.py` | Quét định kỳ + gửi tóm tắt |

> ⚠️ **Chỉ chạy 1 worker cho Web.** Job queue và rate limit là *in-process*; nhiều worker sẽ khiến mỗi worker giữ state riêng và hỏng logic. Dùng nhiều **thread** (`--threads`) để chịu tải, không tăng `--workers`. Nếu cần scale ngang thật sự, chuyển job queue sang Redis/RQ/Celery (xem `ARCHITECTURE.md`).

---

## 1. Chuẩn bị biến môi trường

Tối thiểu cần `GEMINI_API_KEY`. Bot cần thêm `TELEGRAM_BOT_TOKEN`. Xem đầy đủ trong `.env.example`.

Trên máy tự host: tạo file `.env` (không commit). Trên nền tảng cloud: khai báo qua phần **Environment Variables** của dịch vụ, **đừng** đưa `.env` vào image (đã loại trong `.dockerignore`).

---

## 2. Docker (một tiến trình)

```bash
docker build -t market-sentiment-bot .

# Web UI
docker run -d --name msb-web -p 5000:5000 --env-file .env \
  -v "$(pwd)/data:/app/data" -v "$(pwd)/reports:/app/reports" \
  market-sentiment-bot

# Telegram bot (ghi đè lệnh mặc định)
docker run -d --name msb-bot --env-file .env \
  -v "$(pwd)/data:/app/data" market-sentiment-bot python bot.py

# Scheduler
docker run -d --name msb-scheduler --env-file .env \
  -v "$(pwd)/data:/app/data" market-sentiment-bot python scheduler.py
```

Mount `data/` và `reports/` ra volume để giữ lịch sử và biểu đồ qua các lần restart.

---

## 3. Docker Compose (cả 3 tiến trình)

```bash
docker compose up -d --build     # bật web + bot + scheduler
docker compose logs -f            # xem log
docker compose down               # dừng
```

Sửa `docker-compose.yml` để tắt bớt service không cần (vd bỏ `bot` nếu chỉ dùng Web).

---

## 4. Railway

1. Tạo project mới → **Deploy from GitHub repo** (chọn repo này).
2. Railway tự nhận `Dockerfile` và build. App lắng nghe cổng `$PORT` (Dockerfile đã xử lý).
3. Vào tab **Variables** thêm `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, ... (theo `.env.example`).
4. (Tùy chọn) thêm **Volume** gắn vào `/app/data` để giữ lịch sử.
5. Muốn chạy bot/scheduler: tạo thêm service từ cùng repo, đặt **Custom Start Command** là `python bot.py` hoặc `python scheduler.py`.

---

## 5. Render

- **Web Service**: Runtime Docker (hoặc dùng `Procfile`). Start command tự lấy từ Dockerfile/Procfile `web`. Thêm biến môi trường trong dashboard. Gắn **Disk** vào `/app/data` để lưu bền.
- **Background Worker**: tạo service loại *Background Worker*, start command `python scheduler.py` (và/hoặc `python bot.py`).

---

## 6. Kiểm tra sau khi deploy

- Mở URL công khai → thấy form nhập chủ đề.
- Thử một chủ đề → trang "đang xử lý" tự refresh rồi ra kết quả.
- `GET /api/status/<job_id>` trả JSON trạng thái (dùng để healthcheck nhẹ).

> 🔒 Web **chưa có xác thực người dùng**. Nếu mở công khai, đặt reverse proxy có auth (hoặc basic auth) phía trước, và cân nhắc siết `WEB_RATE_MAX`/`WEB_RATE_WINDOW`.
