"""Cấu hình chung cho test: đảm bảo import được module ở thư mục gốc dự án."""
import os
import sys

# Thêm thư mục gốc dự án vào sys.path để import scraper, engine, reporter...
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
