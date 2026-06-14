import requests
import urllib.parse
import re
import html


def _clean(text):
    """Dọn rác cơ bản: bỏ thẻ HTML, giải mã ký tự đặc biệt, gộp xuống dòng."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)   # bỏ thẻ HTML
    text = html.unescape(text)              # &amp; -> &, &#39; -> '
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text)        # gộp khoảng trắng thừa
    return text.strip()


def fetch_hackernews(query, limit=50):
    """Cào tiêu đề + nội dung bài viết/bình luận từ Hacker News (Algolia API)."""
    encoded = urllib.parse.quote(query)
    url = (
        f"https://hn.algolia.com/api/v1/search?query={encoded}"
        f"&tags=(story,comment)&hitsPerPage={limit}"
    )
    texts = []
    try:
        print(f"[*] ⛏️ Đang cào dữ liệu từ Hacker News cho: '{query}'...")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        for hit in r.json().get("hits", []):
            # Story dùng 'title', comment dùng 'comment_text'
            raw = hit.get("title") or hit.get("comment_text") or hit.get("story_text") or ""
            cleaned = _clean(raw)
            if len(cleaned) > 20:
                texts.append(cleaned)
        print(f"[+] ✅ Hacker News: lấy được {len(texts)} ý kiến.")
    except Exception as e:
        print(f"[!] ⚠️ Lỗi khi cào Hacker News: {e}")
    return texts


def fetch_google_news(query, limit=50, lang="en", country="US"):
    """Cào tiêu đề + mô tả tin tức từ Google News RSS theo ngôn ngữ/quốc gia."""
    encoded = urllib.parse.quote(query)
    hl = f"{lang}-{country}"
    ceid = f"{country}:{lang}"
    url = (
        f"https://news.google.com/rss/search?q={encoded}"
        f"&hl={hl}&gl={country}&ceid={ceid}"
    )
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SentimentBot/1.0)"}
    texts = []
    try:
        print(f"[*] ⛏️ Đang cào tin tức từ Google News ({hl}) cho: '{query}'...")
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        # RSS đơn giản: tách theo <item>, lấy <title> và <description>
        items = re.findall(r"<item>(.*?)</item>", r.text, re.DOTALL)
        for item in items[:limit]:
            title_m = re.search(r"<title>(.*?)</title>", item, re.DOTALL)
            desc_m = re.search(r"<description>(.*?)</description>", item, re.DOTALL)
            title = _clean(title_m.group(1)) if title_m else ""
            desc = _clean(desc_m.group(1)) if desc_m else ""
            combined = f"{title}. {desc}".strip()
            if len(combined) > 20:
                texts.append(combined)
        print(f"[+] ✅ Google News: lấy được {len(texts)} tin.")
    except Exception as e:
        print(f"[!] ⚠️ Lỗi khi cào Google News: {e}")
    return texts


def fetch_market_data(query, limit=50):
    """
    Tổng hợp ý kiến/tin tức từ nhiều nguồn (Hacker News + Google News)
    để làm nguồn dữ liệu cho AI phân tích tâm lý thị trường.
    Cào tin cả tiếng Anh (toàn cầu) lẫn tiếng Việt để bao quát dư luận.
    """
    all_texts = []
    all_texts.extend(fetch_hackernews(query, limit))
    all_texts.extend(fetch_google_news(query, limit, lang="en", country="US"))
    all_texts.extend(fetch_google_news(query, limit, lang="vi", country="VN"))

    # Khử trùng lặp mà vẫn giữ thứ tự
    seen = set()
    unique = []
    for t in all_texts:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            unique.append(t)

    print(f"[+] 📦 Tổng cộng {len(unique)} đoạn dữ liệu (đã khử trùng lặp).")
    return unique


if __name__ == "__main__":
    # Test thử trực tiếp khi chạy đúng file này trong terminal
    target_keyword = "iPhone"
    data = fetch_market_data(target_keyword, limit=30)

    print("\n" + "=" * 50)
    print("--- XEM THỬ MỘT VÀI DỮ LIỆU ĐÀO ĐƯỢC ---")
    print("=" * 50)

    for idx, c in enumerate(data[:5]):
        print(f"\n[Bài {idx+1}]: {c[:300]}...")
