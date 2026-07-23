import os
import time
import requests
import urllib.parse
import re
import html
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()

# Deadline tổng cho toàn bộ bước cào dữ liệu (giây). Tránh treo request quá lâu.
FETCH_TOTAL_TIMEOUT = int(os.getenv("FETCH_TOTAL_TIMEOUT", "45"))

# Các khoảng thời gian hợp lệ để lọc dữ liệu theo độ mới.
TIME_RANGES = ("week", "month", "year")
_RANGE_DAYS = {"week": 7, "month": 30, "year": 365}
_GNEWS_WHEN = {"week": "when:7d", "month": "when:30d", "year": "when:1y"}


def _time_filters(time_range):
    """Chuyển `time_range` thành tham số lọc cho từng nguồn.

    Trả về dict: {hn_since (epoch|None), gnews_suffix (str), reddit_t (str), yt_after (str|None)}.
    `time_range` không hợp lệ / None => không lọc (Reddit giữ mặc định 'month' như trước).
    """
    days = _RANGE_DAYS.get(time_range)
    if not days:
        return {"hn_since": None, "gnews_suffix": "", "reddit_t": "month", "yt_after": None}
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return {
        "hn_since": int(cutoff.timestamp()),
        "gnews_suffix": " " + _GNEWS_WHEN[time_range],
        "reddit_t": time_range,  # Reddit chấp nhận week/month/year
        "yt_after": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _clean(text):
    """Dọn rác cơ bản: bỏ thẻ HTML, giải mã ký tự đặc biệt, gộp xuống dòng."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)   # bỏ thẻ HTML
    text = html.unescape(text)              # &amp; -> &, &#39; -> '
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text)        # gộp khoảng trắng thừa
    return text.strip()


def _parse_rss_items(xml_text, limit):
    """Parse RSS bằng XML parser chuẩn, fallback regex nếu XML hỏng.

    Trả về list các tuple (title, description, link) tối đa `limit` phần tử.
    """
    results = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.iter("item"):
            title = item.findtext("title") or ""
            desc = item.findtext("description") or ""
            link = item.findtext("link") or ""
            results.append((title, desc, link))
            if len(results) >= limit:
                break
        return results
    except ET.ParseError as e:
        print(f"[!] ⚠️ RSS lỗi XML, dùng parser dự phòng: {e}")

    # Fallback: tách thô bằng regex nếu XML không hợp lệ
    items = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL)
    for item in items[:limit]:
        title_m = re.search(r"<title>(.*?)</title>", item, re.DOTALL)
        desc_m = re.search(r"<description>(.*?)</description>", item, re.DOTALL)
        link_m = re.search(r"<link>(.*?)</link>", item, re.DOTALL)
        title = title_m.group(1) if title_m else ""
        desc = desc_m.group(1) if desc_m else ""
        link = link_m.group(1) if link_m else ""
        results.append((title, desc, link))
    return results


def fetch_hackernews(query, limit=50, time_range=None):
    """Cào tiêu đề + nội dung bài viết/bình luận từ Hacker News (Algolia API)."""
    encoded = urllib.parse.quote(query)
    url = (
        f"https://hn.algolia.com/api/v1/search?query={encoded}"
        f"&tags=(story,comment)&hitsPerPage={limit}"
    )
    hn_since = _time_filters(time_range)["hn_since"]
    if hn_since:
        url += f"&numericFilters=created_at_i>{hn_since}"
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
                obj_id = hit.get("objectID")
                item_url = f"https://news.ycombinator.com/item?id={obj_id}" if obj_id else None
                title = _clean(hit.get("title") or hit.get("story_title") or "") or cleaned[:80]
                texts.append({"text": cleaned, "url": item_url,
                              "title": title, "source": "Hacker News"})
        print(f"[+] ✅ Hacker News: lấy được {len(texts)} ý kiến.")
    except Exception as e:
        print(f"[!] ⚠️ Lỗi khi cào Hacker News: {e}")
    return texts


def fetch_google_news(query, limit=50, lang="en", country="US", time_range=None):
    """Cào tiêu đề + mô tả tin tức từ Google News RSS theo ngôn ngữ/quốc gia."""
    # Google News hỗ trợ toán tử when: trong truy vấn để lọc theo độ mới.
    query = query + _time_filters(time_range)["gnews_suffix"]
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
        for title, desc, link in _parse_rss_items(r.text, limit):
            clean_title = _clean(title)
            combined = f"{clean_title}. {_clean(desc)}".strip()
            if len(combined) > 20:
                texts.append({"text": combined, "url": _clean(link) or None,
                              "title": clean_title or combined[:80],
                              "source": f"Google News ({hl})"})
        print(f"[+] ✅ Google News: lấy được {len(texts)} tin.")
    except Exception as e:
        print(f"[!] ⚠️ Lỗi khi cào Google News: {e}")
    return texts


def fetch_youtube_comments(query, limit=50, time_range=None):
    """
    Cào bình luận từ các video YouTube liên quan tới chủ đề (YouTube Data API v3).
    Chỉ chạy nếu có YOUTUBE_API_KEY trong .env, nếu không thì bỏ qua êm.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return []  # chưa cấu hình -> bỏ qua

    yt_after = _time_filters(time_range)["yt_after"]
    texts = []
    try:
        print(f"[*] ⛏️ Đang cào bình luận từ YouTube cho: '{query}'...")
        # 1) Tìm vài video liên quan nhất
        search_url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&q={urllib.parse.quote(query)}"
            f"&type=video&maxResults=5&relevanceLanguage=vi&key={api_key}"
        )
        if yt_after:
            search_url += f"&publishedAfter={yt_after}"
        r = requests.get(search_url, timeout=20)
        r.raise_for_status()
        # Map videoId -> tiêu đề video để trích dẫn nguồn cho gọn.
        video_titles = {}
        for it in r.json().get("items", []):
            vid = it.get("id", {}).get("videoId")
            if vid:
                video_titles[vid] = _clean(it.get("snippet", {}).get("title", "")) or "Video YouTube"
        video_ids = list(video_titles.keys())

        # 2) Lấy comment của từng video cho tới khi đủ limit
        per_video = max(5, limit // max(1, len(video_ids))) if video_ids else 0
        for vid in video_ids:
            if len(texts) >= limit:
                break
            video_url = f"https://www.youtube.com/watch?v={vid}"
            ct_url = (
                "https://www.googleapis.com/youtube/v3/commentThreads"
                f"?part=snippet&videoId={vid}&maxResults={min(per_video, 100)}"
                f"&order=relevance&textFormat=plainText&key={api_key}"
            )
            try:
                cr = requests.get(ct_url, timeout=20)
                cr.raise_for_status()
                for item in cr.json().get("items", []):
                    snippet = (
                        item.get("snippet", {})
                        .get("topLevelComment", {})
                        .get("snippet", {})
                    )
                    cleaned = _clean(snippet.get("textDisplay", ""))
                    if len(cleaned) > 20:
                        texts.append({"text": cleaned, "url": video_url,
                                      "title": video_titles.get(vid, "Video YouTube"),
                                      "source": "YouTube"})
            except Exception:
                continue  # video tắt comment hoặc lỗi lẻ -> bỏ qua video đó
        print(f"[+] ✅ YouTube: lấy được {len(texts)} bình luận.")
    except Exception as e:
        print(f"[!] ⚠️ Lỗi khi cào YouTube: {e}")
    return texts


# Cache token Reddit kèm thời điểm hết hạn để tự xin lại khi cần.
_reddit_token = {"value": None, "expires_at": 0.0}


def _invalidate_reddit_token():
    """Xóa token đang cache (gọi khi gặp 401 để lần sau xin token mới)."""
    _reddit_token["value"] = None
    _reddit_token["expires_at"] = 0.0


def _get_reddit_token(force_refresh=False):
    """Lấy access token theo luồng client-credentials (app-only OAuth).

    Tự động xin token mới nếu chưa có, đã hết hạn, hoặc bị ép refresh.
    """
    # Còn hạn (chừa 60s an toàn) và không bị ép refresh -> dùng lại
    if not force_refresh and _reddit_token["value"] and time.time() < _reddit_token["expires_at"] - 60:
        return _reddit_token["value"]

    cid = os.getenv("REDDIT_CLIENT_ID")
    secret = os.getenv("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        return None
    try:
        auth = requests.auth.HTTPBasicAuth(cid, secret)
        ua = os.getenv("REDDIT_USER_AGENT", "python:sentiment_bot:v1.0")
        r = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": ua},
            timeout=20,
        )
        r.raise_for_status()
        payload = r.json()
        token = payload.get("access_token")
        expires_in = payload.get("expires_in", 3600)  # Reddit thường trả 3600s
        _reddit_token["value"] = token
        _reddit_token["expires_at"] = time.time() + float(expires_in)
        return token
    except Exception as e:
        print(f"[!] ⚠️ Không lấy được token Reddit: {e}")
        _invalidate_reddit_token()
        return None


def fetch_reddit(query, limit=50, time_range=None):
    """
    Cào bài đăng Reddit qua OAuth chính thức (oauth.reddit.com).
    Chỉ chạy nếu có REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET trong .env.
    """
    cid = os.getenv("REDDIT_CLIENT_ID")
    secret = os.getenv("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        return []  # chưa cấu hình -> bỏ qua

    token = _get_reddit_token()
    if not token:
        return []

    reddit_t = _time_filters(time_range)["reddit_t"]
    texts = []
    ua = os.getenv("REDDIT_USER_AGENT", "python:sentiment_bot:v1.0")
    url = (
        "https://oauth.reddit.com/search"
        f"?q={urllib.parse.quote(query)}&sort=hot&t={reddit_t}&limit={limit}"
    )
    try:
        print(f"[*] ⛏️ Đang cào bài đăng từ Reddit (OAuth) cho: '{query}'...")
        headers = {"Authorization": f"bearer {token}", "User-Agent": ua}
        r = requests.get(url, headers=headers, timeout=20)

        # Token hết hạn/không hợp lệ -> xin token mới và thử lại đúng 1 lần
        if r.status_code == 401:
            print("[!] ⚠️ Token Reddit hết hạn, đang xin token mới...")
            token = _get_reddit_token(force_refresh=True)
            if not token:
                return []
            headers["Authorization"] = f"bearer {token}"
            r = requests.get(url, headers=headers, timeout=20)

        r.raise_for_status()
        for post in r.json().get("data", {}).get("children", []):
            d = post.get("data", {})
            title = _clean(d.get("title", ""))
            combined = _clean(f"{d.get('title', '')}. {d.get('selftext', '')}")
            if len(combined) > 20:
                permalink = d.get("permalink")
                post_url = f"https://www.reddit.com{permalink}" if permalink else d.get("url")
                texts.append({"text": combined, "url": post_url,
                              "title": title or combined[:80], "source": "Reddit"})
        print(f"[+] ✅ Reddit: lấy được {len(texts)} bài đăng.")
    except Exception as e:
        print(f"[!] ⚠️ Lỗi khi cào Reddit: {e}")
    return texts


def fetch_market_data(query, limit=50, time_range=None):
    """
    Tổng hợp ý kiến/tin tức từ nhiều nguồn để làm nguồn dữ liệu cho AI.
    Nguồn luôn bật: Hacker News + Google News (Anh + Việt).
    Nguồn tùy chọn (chỉ bật khi có credentials trong .env): YouTube, Reddit OAuth.

    `time_range` (week/month/year/None) lọc dữ liệu theo độ mới ở từng nguồn.
    Các nguồn được gọi SONG SONG để giảm độ trễ, kèm deadline tổng
    (FETCH_TOTAL_TIMEOUT) để không treo request quá lâu.
    """
    # (tên nguồn, hàm chạy) — thứ tự này cũng là thứ tự ưu tiên khi gộp kết quả.
    sources = [
        ("Hacker News", lambda: fetch_hackernews(query, limit, time_range)),
        ("Google News (EN)",
         lambda: fetch_google_news(query, limit, lang="en", country="US", time_range=time_range)),
        ("Google News (VI)",
         lambda: fetch_google_news(query, limit, lang="vi", country="VN", time_range=time_range)),
        ("YouTube", lambda: fetch_youtube_comments(query, limit, time_range)),  # bỏ qua nếu chưa có key
        ("Reddit", lambda: fetch_reddit(query, limit, time_range)),             # bỏ qua nếu chưa có key
    ]

    results_by_source = {}
    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        future_to_name = {executor.submit(fn): name for name, fn in sources}
        try:
            for future in as_completed(future_to_name, timeout=FETCH_TOTAL_TIMEOUT):
                name = future_to_name[future]
                try:
                    results_by_source[name] = future.result()
                except Exception as e:
                    print(f"[!] ⚠️ Nguồn '{name}' lỗi: {e}")
                    results_by_source[name] = []
        except TimeoutError:
            done = set(results_by_source.keys())
            pending = [n for n in future_to_name.values() if n not in done]
            print(f"[!] ⚠️ Quá deadline {FETCH_TOTAL_TIMEOUT}s, bỏ qua nguồn chậm: {', '.join(pending)}")

    # Gộp theo thứ tự nguồn đã định để kết quả ổn định
    all_texts = []
    for name, _ in sources:
        all_texts.extend(results_by_source.get(name, []))

    # Khử trùng lặp theo nội dung text mà vẫn giữ thứ tự.
    # Hỗ trợ cả item dạng dict {"text", "url", ...} lẫn str thuần (để tương thích ngược).
    seen = set()
    unique = []
    for t in all_texts:
        text = t["text"] if isinstance(t, dict) else t
        key = text.lower()
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
        text = c["text"] if isinstance(c, dict) else c
        url = c.get("url") if isinstance(c, dict) else None
        print(f"\n[Bài {idx+1}]: {text[:300]}...")
        if url:
            print(f"   🔗 {url}")
