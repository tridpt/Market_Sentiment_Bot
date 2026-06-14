"""Test cho scraper.py - tập trung vào hàm dọn dữ liệu _clean và logic bỏ qua nguồn tùy chọn."""
import scraper


def test_clean_removes_html_tags():
    assert scraper._clean("<p>Hello <b>world</b></p>") == "Hello world"


def test_clean_unescapes_entities():
    assert scraper._clean("Tom &amp; Jerry &#39;test&#39;") == "Tom & Jerry 'test'"


def test_clean_collapses_whitespace():
    assert scraper._clean("a\n\n  b\t\tc") == "a b c"


def test_clean_empty():
    assert scraper._clean("") == ""
    assert scraper._clean(None) == ""


def test_youtube_skips_without_key(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    assert scraper.fetch_youtube_comments("anything") == []


def test_reddit_skips_without_credentials(monkeypatch):
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    assert scraper.fetch_reddit("anything") == []


def test_fetch_market_data_dedupes(monkeypatch):
    # Giả lập các nguồn trả về dữ liệu trùng nhau (khác hoa thường)
    monkeypatch.setattr(scraper, "fetch_hackernews", lambda q, l=50: ["Apple is great", "apple IS great"])
    monkeypatch.setattr(scraper, "fetch_google_news", lambda q, l=50, lang="en", country="US": ["New phone"])
    monkeypatch.setattr(scraper, "fetch_youtube_comments", lambda q, l=50: [])
    monkeypatch.setattr(scraper, "fetch_reddit", lambda q, l=50: [])

    result = scraper.fetch_market_data("Apple", limit=50)
    # "Apple is great" và "apple IS great" là trùng -> chỉ giữ 1
    assert len(result) == 2
    assert "Apple is great" in result
    assert "New phone" in result
