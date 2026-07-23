# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Cài phụ thuộc trước để tận dụng cache layer khi chỉ code thay đổi.
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn==23.0.0

COPY . .

# Thư mục dữ liệu/artefact sinh ra lúc chạy (nên mount volume để giữ lại).
RUN mkdir -p data reports/charts assets

EXPOSE 5000

# QUAN TRỌNG: job queue + rate limit là IN-PROCESS -> chỉ dùng 1 worker (nhiều thread).
# Chạy nhiều worker sẽ khiến mỗi worker có state riêng, hỏng logic job/rate limit.
# Railway/Render đặt cổng qua biến $PORT; mặc định 5000 khi chạy local.
CMD ["sh", "-c", "gunicorn --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:${PORT:-5000} webapp:app"]
