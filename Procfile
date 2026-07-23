# Dành cho nền tảng buildpack (Render / Heroku-style). Job queue + rate limit in-process -> 1 worker.
web: gunicorn --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:$PORT webapp:app
worker: python scheduler.py
