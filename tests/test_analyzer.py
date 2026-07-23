"""Test cho analyzer.validate_sentiment - kiểm tra và chuẩn hóa JSON do AI trả về.
Không gọi API thật; chỉ test logic validation thuần túy.
"""
import analyzer


VALID = {
    "tong_quan": "Tích Cực",
    "phan_tram_tich_cuc": 70,
    "phan_tram_tieu_cuc": 20,
    "phan_tram_trung_lap": 10,
    "top_3_khen": ["a", "b", "c"],
    "top_3_che": ["x", "y", "z"],
    "ket_luan_ngan": "Ổn.",
}


def test_valid_passes_through():
    ok, cleaned = analyzer.validate_sentiment(VALID)
    assert ok is True
    assert cleaned["phan_tram_tich_cuc"] == 70
    assert cleaned["tong_quan"] == "Tích Cực"


def test_not_dict_rejected():
    ok, msg = analyzer.validate_sentiment("không phải dict")
    assert ok is False


def test_missing_keys_rejected():
    ok, msg = analyzer.validate_sentiment({"tong_quan": "Tốt"})
    assert ok is False
    assert "Thiếu" in msg


def test_percent_normalized_to_100():
    data = {**VALID, "phan_tram_tich_cuc": 50,
            "phan_tram_tieu_cuc": 30, "phan_tram_trung_lap": 40}  # tổng = 120
    ok, cleaned = analyzer.validate_sentiment(data)
    assert ok is True
    total = (cleaned["phan_tram_tich_cuc"] + cleaned["phan_tram_tieu_cuc"]
             + cleaned["phan_tram_trung_lap"])
    assert total == 100


def test_percent_out_of_range_clamped():
    data = {**VALID, "phan_tram_tich_cuc": 150,
            "phan_tram_tieu_cuc": -10, "phan_tram_trung_lap": 5}
    ok, cleaned = analyzer.validate_sentiment(data)
    assert ok is True
    assert 0 <= cleaned["phan_tram_tich_cuc"] <= 100
    assert 0 <= cleaned["phan_tram_tieu_cuc"] <= 100


def test_non_numeric_percent_rejected():
    data = {**VALID, "phan_tram_tich_cuc": "rất cao"}
    ok, msg = analyzer.validate_sentiment(data)
    assert ok is False


def test_all_zero_percent_rejected():
    data = {**VALID, "phan_tram_tich_cuc": 0,
            "phan_tram_tieu_cuc": 0, "phan_tram_trung_lap": 0}
    ok, msg = analyzer.validate_sentiment(data)
    assert ok is False


def test_lists_trimmed_to_three():
    data = {**VALID, "top_3_khen": ["1", "2", "3", "4", "5"]}
    ok, cleaned = analyzer.validate_sentiment(data)
    assert ok is True
    assert len(cleaned["top_3_khen"]) == 3


def test_non_list_praise_rejected():
    data = {**VALID, "top_3_khen": "không phải list"}
    ok, msg = analyzer.validate_sentiment(data)
    assert ok is False
