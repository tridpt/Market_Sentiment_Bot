"""Test cho reporter.py - định dạng & xuất báo cáo."""
import os
import json

import reporter


SAMPLE = {
    "tong_quan": "Trái Chiều",
    "phan_tram_tich_cuc": 40,
    "phan_tram_tieu_cuc": 35,
    "phan_tram_trung_lap": 25,
    "top_3_khen": ["Camera tốt", "Pin trâu", "Màn đẹp"],
    "top_3_che": ["Giá cao", "Nóng máy", "Sạc chậm"],
    "ket_luan_ngan": "Tổng thể ổn nhưng giá chát.",
}


def test_slug_basic():
    assert reporter._slug("iPhone 15 Pro") == "iphone_15_pro"


def test_slug_special_chars():
    # Ký tự đặc biệt bị loại, khoảng trắng thành gạch dưới
    assert reporter._slug("Tesla!!! @#$ Model 3") == "tesla_model_3"


def test_slug_empty_fallback():
    assert reporter._slug("!!!") == "report"


def test_format_text_contains_key_parts():
    out = reporter.format_text("iPhone", SAMPLE)
    assert "IPHONE" in out
    assert "40%" in out and "35%" in out and "25%" in out
    assert "Camera tốt" in out
    assert "Giá cao" in out
    assert "Tổng thể ổn nhưng giá chát." in out


def test_format_markdown_structure():
    md = reporter.format_markdown("Tesla", SAMPLE)
    assert md.startswith("# 📊")
    assert "Tesla" in md
    assert "**40%**" in md
    assert "1. Camera tốt" in md
    assert "> Tổng thể ổn nhưng giá chát." in md


def test_format_telegram_uses_html():
    out = reporter.format_telegram("VinFast", SAMPLE)
    assert "<b>" in out
    assert "VINFAST" in out
    assert "40%" in out


def test_save_report_md(tmp_path, monkeypatch):
    monkeypatch.setattr(reporter, "REPORTS_DIR", str(tmp_path))
    path = reporter.save_report("My Topic", SAMPLE, fmt="md")
    assert os.path.exists(path)
    assert path.endswith(".md")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "My Topic" in content


def test_save_report_json(tmp_path, monkeypatch):
    monkeypatch.setattr(reporter, "REPORTS_DIR", str(tmp_path))
    path = reporter.save_report("My Topic", SAMPLE, fmt="json")
    assert path.endswith(".json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["topic"] == "My Topic"
    assert data["result"]["phan_tram_tich_cuc"] == 40
