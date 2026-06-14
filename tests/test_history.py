"""Test cho history.py - lưu/đọc lịch sử phân tích."""
import importlib

import history as history_mod


def _fresh_history(tmp_path, monkeypatch):
    """Trỏ history về thư mục tạm để test không đụng dữ liệu thật."""
    monkeypatch.setattr(history_mod, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(history_mod, "HISTORY_FILE", str(tmp_path / "history.json"))
    return history_mod


SAMPLE = {
    "tong_quan": "Tích Cực",
    "phan_tram_tich_cuc": 60,
    "phan_tram_tieu_cuc": 20,
    "phan_tram_trung_lap": 20,
    "top_3_khen": ["a", "b", "c"],
    "top_3_che": ["x", "y", "z"],
    "ket_luan_ngan": "Ổn.",
}


def test_load_all_empty(tmp_path, monkeypatch):
    h = _fresh_history(tmp_path, monkeypatch)
    assert h.load_all() == []


def test_save_and_load(tmp_path, monkeypatch):
    h = _fresh_history(tmp_path, monkeypatch)
    h.save_record("iPhone", SAMPLE, source_count=10)
    records = h.load_all()
    assert len(records) == 1
    assert records[0]["topic"] == "iPhone"
    assert records[0]["phan_tram_tich_cuc"] == 60
    assert records[0]["source_count"] == 10
    assert records[0]["full_result"] == SAMPLE


def test_get_history_for_topic_case_insensitive(tmp_path, monkeypatch):
    h = _fresh_history(tmp_path, monkeypatch)
    h.save_record("Tesla", SAMPLE, source_count=5)
    h.save_record("TESLA", SAMPLE, source_count=8)
    h.save_record("VinFast", SAMPLE, source_count=3)
    tesla = h.get_history_for_topic("tesla")
    assert len(tesla) == 2


def test_list_topics_counts(tmp_path, monkeypatch):
    h = _fresh_history(tmp_path, monkeypatch)
    h.save_record("A", SAMPLE)
    h.save_record("A", SAMPLE)
    h.save_record("B", SAMPLE)
    counts = h.list_topics()
    assert counts["A"] == 2
    assert counts["B"] == 1


def test_load_all_corrupt_file(tmp_path, monkeypatch):
    h = _fresh_history(tmp_path, monkeypatch)
    (tmp_path / "history.json").write_text("{not valid json", encoding="utf-8")
    # File hỏng không nên làm crash, trả list rỗng
    assert h.load_all() == []
