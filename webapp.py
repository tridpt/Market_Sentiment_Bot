"""Web UI đơn giản (Flask) cho hệ thống phân tích tâm lý thị trường.
Chạy: python webapp.py  -> mở http://127.0.0.1:5000
"""
import os
from flask import (Flask, request, render_template_string, send_from_directory,
                   redirect, url_for, jsonify)

from engine import run_analysis, run_comparison, parse_topics
from scraper import TIME_RANGES
from jobs import JobManager
from ratelimit import RateLimiter
import history
import charts

app = Flask(__name__)
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

# Giới hạn để tránh lạm dụng: một request không thể kích hoạt quá nhiều pipeline tốn phí.
MAX_TOPIC_LEN = 200   # độ dài tối đa của ô nhập
MAX_COMPARE_TOPICS = 4  # số chủ đề tối đa cho một lần so sánh

# Hàng đợi job nền: request chỉ tạo job rồi trả ngay, không bị khóa khi cào + gọi AI.
job_manager = JobManager(
    max_workers=int(os.getenv("WEB_JOB_WORKERS", "2")),
    ttl=int(os.getenv("WEB_JOB_TTL", "1800")),
)
# Rate limit theo IP để chặn spam các job tốn phí.
limiter = RateLimiter(
    max_requests=int(os.getenv("WEB_RATE_MAX", "10")),
    window=int(os.getenv("WEB_RATE_WINDOW", "60")),
)


def _client_ip():
    """Lấy IP client, ưu tiên X-Forwarded-For khi chạy sau reverse proxy."""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"

PAGE = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {% if loading %}<meta http-equiv="refresh" content="2">{% endif %}
  <title>Market Sentiment Bot</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; background:#0f1226; color:#e8eaf2; margin:0; padding:0; }
    .wrap { max-width: 880px; margin: 0 auto; padding: 32px 20px 64px; }
    h1 { font-size: 26px; margin-bottom: 4px; }
    .sub { color:#9aa0c0; margin-bottom: 24px; font-size: 14px; }
    form { display:flex; gap:10px; margin-bottom: 28px; flex-wrap: wrap; }
    input[type=text] { flex:1; min-width: 220px; padding:13px 16px; border-radius:10px; border:1px solid #2a2f55; background:#1a1e3a; color:#fff; font-size:15px; }
    select { padding:13px 12px; border-radius:10px; border:1px solid #2a2f55; background:#1a1e3a; color:#fff; font-size:15px; }
    button { padding:13px 24px; border:0; border-radius:10px; background:#5468ff; color:#fff; font-size:15px; font-weight:600; cursor:pointer; }
    button:hover { background:#4055e0; }
    .card { background:#1a1e3a; border:1px solid #2a2f55; border-radius:14px; padding:24px; margin-bottom:20px; }
    .overall { font-size:20px; font-weight:700; margin-bottom:16px; }
    .bars { margin:16px 0; }
    .bar-row { display:flex; align-items:center; gap:10px; margin-bottom:8px; font-size:14px; }
    .bar-label { width:80px; }
    .bar-track { flex:1; background:#0f1226; border-radius:6px; overflow:hidden; height:22px; }
    .bar-fill { height:100%; display:flex; align-items:center; padding-left:8px; font-size:12px; color:#fff; white-space:nowrap; }
    .pos { background:#2ecc71; } .neg { background:#e74c3c; } .neu { background:#95a5a6; }
    h3 { margin:18px 0 8px; font-size:16px; }
    ul { margin:0; padding-left:20px; line-height:1.7; }
    .concl { font-style:italic; color:#c8cdf0; border-left:3px solid #5468ff; padding-left:14px; margin-top:10px; }
    .sources { margin-top:8px; font-size:13px; }
    .sources li { margin-bottom:4px; }
    .sources a { color:#8fa8ff; text-decoration:none; word-break:break-all; }
    .sources a:hover { text-decoration:underline; }
    .src-tag { color:#7f86ad; font-size:11px; }
    .err { background:#3a1a25; border:1px solid #e74c3c; color:#ffb3c0; padding:14px; border-radius:10px; }
    img.chart { max-width:100%; border-radius:12px; margin-top:16px; background:#fff; }
    .loading { color:#9aa0c0; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>📊 Market Sentiment Bot</h1>
    <div class="sub">Đo nhiệt dư luận thị trường bằng AI (Hacker News + Google News + Gemini)</div>
    <form method="get" action="/">
      <input type="text" name="topic" placeholder="Nhập sản phẩm/chủ đề (VD: Cybertruck, VinFast...)" value="{{ topic or '' }}" autofocus>
      <select name="range" title="Lọc theo độ mới của dữ liệu">
        <option value="" {% if not selected_range %}selected{% endif %}>Mọi thời điểm</option>
        <option value="week" {% if selected_range == 'week' %}selected{% endif %}>7 ngày qua</option>
        <option value="month" {% if selected_range == 'month' %}selected{% endif %}>30 ngày qua</option>
        <option value="year" {% if selected_range == 'year' %}selected{% endif %}>1 năm qua</option>
      </select>
      <button type="submit">Phân tích</button>
    </form>

    {% if error %}
      <div class="err">⚠️ {{ error }}</div>
    {% endif %}

    {% if loading %}
      <div class="card">
        <div class="loading">⏳ Đang cào dữ liệu &amp; phân tích... Trang sẽ tự cập nhật sau vài giây.</div>
      </div>
    {% endif %}

    {% if result %}
      <div class="card">
        <div class="overall">Thái độ tổng quan: {{ result.tong_quan }}</div>
        <div class="sub">Dựa trên {{ source_count }} đoạn dữ liệu</div>
        <div class="bars">
          <div class="bar-row"><div class="bar-label">✅ Tích cực</div>
            <div class="bar-track"><div class="bar-fill pos" style="width:{{ result.phan_tram_tich_cuc }}%">{{ result.phan_tram_tich_cuc }}%</div></div></div>
          <div class="bar-row"><div class="bar-label">❌ Tiêu cực</div>
            <div class="bar-track"><div class="bar-fill neg" style="width:{{ result.phan_tram_tieu_cuc }}%">{{ result.phan_tram_tieu_cuc }}%</div></div></div>
          <div class="bar-row"><div class="bar-label">⚪ Trung lập</div>
            <div class="bar-track"><div class="bar-fill neu" style="width:{{ result.phan_tram_trung_lap }}%">{{ result.phan_tram_trung_lap }}%</div></div></div>
        </div>

        <h3>✅ Top điểm được khen</h3>
        <ul>{% for k in result.top_3_khen %}<li>{{ k }}</li>{% endfor %}</ul>

        <h3>❌ Top điểm bị chê / bức xúc</h3>
        <ul>{% for c in result.top_3_che %}<li>{{ c }}</li>{% endfor %}</ul>

        <h3>💡 Kết luận của chuyên gia AI</h3>
        <div class="concl">{{ result.ket_luan_ngan }}</div>

        {% if sources %}
          <h3>🔗 Nguồn tham khảo</h3>
          <ul class="sources">
            {% for s in sources %}
              <li><a href="{{ s.url }}" target="_blank" rel="noopener noreferrer">{{ s.title }}</a>
                {% if s.source %}<span class="src-tag">({{ s.source }})</span>{% endif %}</li>
            {% endfor %}
          </ul>
        {% endif %}

        {% if pie_url %}<img class="chart" src="{{ pie_url }}" alt="Biểu đồ tròn">{% endif %}
        {% if trend_url %}<img class="chart" src="{{ trend_url }}" alt="Biểu đồ xu hướng">{% endif %}
      </div>
    {% endif %}

    {% if compare_items %}
      <div class="card">
        <div class="overall">⚖️ So sánh: {{ compare_topics }}</div>
        {% if compare_winner %}<div class="sub">🏆 Dư luận tích cực nhất: <b>{{ compare_winner }}</b></div>{% endif %}
        {% for it in compare_items %}
          {% if it.ok %}
            <div style="margin-top:18px; border-top:1px solid #2a2f55; padding-top:14px;">
              <div style="font-weight:600; font-size:16px; margin-bottom:8px;">▶ {{ it.topic }} <span style="color:#9aa0c0; font-weight:400; font-size:13px;">({{ it.result.tong_quan }}, {{ it.source_count }} nguồn)</span></div>
              <div class="bars">
                <div class="bar-row"><div class="bar-label">✅ Tích cực</div>
                  <div class="bar-track"><div class="bar-fill pos" style="width:{{ it.result.phan_tram_tich_cuc }}%">{{ it.result.phan_tram_tich_cuc }}%</div></div></div>
                <div class="bar-row"><div class="bar-label">❌ Tiêu cực</div>
                  <div class="bar-track"><div class="bar-fill neg" style="width:{{ it.result.phan_tram_tieu_cuc }}%">{{ it.result.phan_tram_tieu_cuc }}%</div></div></div>
                <div class="bar-row"><div class="bar-label">⚪ Trung lập</div>
                  <div class="bar-track"><div class="bar-fill neu" style="width:{{ it.result.phan_tram_trung_lap }}%">{{ it.result.phan_tram_trung_lap }}%</div></div></div>
              </div>
            </div>
          {% else %}
            <div style="margin-top:14px; color:#ffb3c0;">⚠️ {{ it.topic }}: {{ it.error }}</div>
          {% endif %}
        {% endfor %}
        {% if compare_url %}<img class="chart" src="{{ compare_url }}" alt="Biểu đồ so sánh">{% endif %}
      </div>
    {% endif %}
  </div>
</body>
</html>
"""


def _render(**kwargs):
    """Render trang với mặc định an toàn cho mọi biến template."""
    defaults = dict(topic=None, result=None, error=None, source_count=0,
                    pie_url=None, trend_url=None, compare_items=None,
                    compare_topics=None, compare_winner=None, compare_url=None,
                    loading=False, sources=None, selected_range="")
    defaults.update(kwargs)
    return render_template_string(PAGE, **defaults)


# ===================== Job workers (chạy nền) =====================

def _analyze_job(topic, time_range=None):
    """Worker: phân tích 1 chủ đề + sinh biểu đồ. Trả payload để render."""
    outcome = run_analysis(topic, limit=50, save_history=True, time_range=time_range)
    if not outcome["ok"]:
        return {"kind": "single", "topic": topic, "error": outcome["error"],
                "selected_range": time_range or ""}

    result = outcome["result"]
    pie_url = trend_url = None
    try:
        pie_path = charts.make_pie_chart(topic, result)
        pie_url = "/charts/" + os.path.basename(pie_path)
    except Exception as e:
        print(f"[!] ⚠️ Không vẽ được biểu đồ tròn cho '{topic}': {e}")
    try:
        recs = history.get_history_for_topic(topic)
        trend_path = charts.make_trend_chart(topic, recs)
        if trend_path:
            trend_url = "/charts/" + os.path.basename(trend_path)
    except Exception as e:
        print(f"[!] ⚠️ Không vẽ được biểu đồ xu hướng cho '{topic}': {e}")

    return {"kind": "single", "topic": topic, "error": None, "result": result,
            "source_count": outcome["source_count"],
            "sources": outcome.get("sources", []),
            "pie_url": pie_url, "trend_url": trend_url,
            "selected_range": time_range or ""}


def _compare_job(topic, time_range=None):
    """Worker: so sánh nhiều chủ đề + sinh biểu đồ cột. Trả payload để render."""
    topics = parse_topics(topic)
    outcome = run_comparison(topics, limit=50, save_history=True, time_range=time_range)
    topics_str = ", ".join(topics)
    if not outcome["ok"]:
        return {"kind": "compare", "topics_str": topics_str, "error": outcome["error"],
                "selected_range": time_range or ""}

    items = outcome["items"]
    ok_items = [it for it in items if it.get("ok")]
    winner = None
    if len(ok_items) >= 2:
        w = max(ok_items, key=lambda it: it["result"].get("phan_tram_tich_cuc", 0))
        winner = f"{w['topic']} ({w['result'].get('phan_tram_tich_cuc', 0)}%)"

    compare_url = None
    try:
        chart_path = charts.make_comparison_chart(items)
        if chart_path:
            compare_url = "/charts/" + os.path.basename(chart_path)
    except Exception as e:
        print(f"[!] ⚠️ Không vẽ được biểu đồ so sánh: {e}")

    return {"kind": "compare", "topics_str": topics_str, "error": None,
            "items": items, "winner": winner, "compare_url": compare_url,
            "selected_range": time_range or ""}


# ===================== Routes =====================

@app.route("/", methods=["GET", "POST"])
def index():
    # Chấp nhận cả GET (?topic=) lẫn POST (form) để tiện bookmark và submit.
    topic = (request.values.get("topic") or "").strip()
    # Chỉ chấp nhận khoảng thời gian hợp lệ, còn lại coi như không lọc.
    time_range = (request.values.get("range") or "").strip().lower()
    if time_range not in TIME_RANGES:
        time_range = None
    selected = time_range or ""

    if not topic:
        return _render(selected_range=selected)

    # Chặn input quá dài (tránh nhồi prompt / lạm dụng)
    if len(topic) > MAX_TOPIC_LEN:
        return _render(topic=topic[:MAX_TOPIC_LEN], selected_range=selected,
                       error=f"Chủ đề quá dài (tối đa {MAX_TOPIC_LEN} ký tự).")

    topics = parse_topics(topic)
    if len(topics) > MAX_COMPARE_TOPICS:
        return _render(topic=topic, selected_range=selected,
                       error=f"Chỉ so sánh tối đa {MAX_COMPARE_TOPICS} chủ đề mỗi lần "
                             f"(bạn nhập {len(topics)}).")

    # Rate limit trước khi tạo job tốn phí
    ip = _client_ip()
    if not limiter.allow(ip):
        wait = limiter.retry_after(ip)
        return _render(topic=topic, selected_range=selected,
                       error=f"Bạn thao tác quá nhanh. Vui lòng thử lại sau {wait} giây."), 429

    # Tạo job nền rồi chuyển sang trang kết quả (không khóa request này)
    worker = _compare_job if len(topics) >= 2 else _analyze_job
    job_id = job_manager.submit(worker, topic, time_range)
    return redirect(url_for("result", job_id=job_id))


@app.route("/result/<job_id>")
def result(job_id):
    job = job_manager.get(job_id)
    if not job:
        return _render(error="Không tìm thấy phiên phân tích (có thể đã hết hạn)."), 404

    if job["status"] in ("queued", "running"):
        return _render(loading=True, topic="")

    if job["status"] == "error":
        return _render(error=f"Lỗi khi xử lý: {job['error']}")

    payload = job["result"] or {}
    selected = payload.get("selected_range", "")
    if payload.get("error"):
        topic = payload.get("topic") or payload.get("topics_str")
        return _render(topic=topic, error=payload["error"], selected_range=selected)

    if payload.get("kind") == "compare":
        return _render(topic=payload["topics_str"], compare_items=payload["items"],
                       compare_topics=payload["topics_str"], selected_range=selected,
                       compare_winner=payload["winner"], compare_url=payload["compare_url"])

    return _render(topic=payload["topic"], result=payload["result"], selected_range=selected,
                   source_count=payload["source_count"], sources=payload.get("sources", []),
                   pie_url=payload["pie_url"], trend_url=payload["trend_url"])


@app.route("/api/status/<job_id>")
def api_status(job_id):
    """Endpoint JSON để client poll trạng thái job."""
    job = job_manager.get(job_id)
    if not job:
        return jsonify({"status": "not_found"}), 404
    return jsonify({"status": job["status"], "error": job["error"]})


@app.route("/charts/<path:filename>")
def serve_chart(filename):
    return send_from_directory(os.path.join(REPORTS_DIR, "charts"), filename)


if __name__ == "__main__":
    print("🌐 Web UI chạy tại http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
