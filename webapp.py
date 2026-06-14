"""Web UI đơn giản (Flask) cho hệ thống phân tích tâm lý thị trường.
Chạy: python webapp.py  -> mở http://127.0.0.1:5000
"""
import os
from flask import Flask, request, render_template_string, send_from_directory

from engine import run_analysis, run_comparison, parse_topics
import history
import charts

app = Flask(__name__)
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

PAGE = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Market Sentiment Bot</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; background:#0f1226; color:#e8eaf2; margin:0; padding:0; }
    .wrap { max-width: 880px; margin: 0 auto; padding: 32px 20px 64px; }
    h1 { font-size: 26px; margin-bottom: 4px; }
    .sub { color:#9aa0c0; margin-bottom: 24px; font-size: 14px; }
    form { display:flex; gap:10px; margin-bottom: 28px; flex-wrap: wrap; }
    input[type=text] { flex:1; min-width: 220px; padding:13px 16px; border-radius:10px; border:1px solid #2a2f55; background:#1a1e3a; color:#fff; font-size:15px; }
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
      <button type="submit">Phân tích</button>
    </form>

    {% if error %}
      <div class="err">⚠️ {{ error }}</div>
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
                    compare_topics=None, compare_winner=None, compare_url=None)
    defaults.update(kwargs)
    return render_template_string(PAGE, **defaults)


@app.route("/")
def index():
    topic = request.args.get("topic", "").strip()
    if not topic:
        return _render()

    # Nếu nhập nhiều chủ đề (vs / phẩy) -> chế độ so sánh
    if len(parse_topics(topic)) >= 2:
        return _compare_view(topic)

    outcome = run_analysis(topic, limit=50, save_history=True)
    if not outcome["ok"]:
        return _render(topic=topic, error=outcome["error"])

    result = outcome["result"]
    # Tạo biểu đồ
    pie_url = trend_url = None
    try:
        pie_path = charts.make_pie_chart(topic, result)
        pie_url = "/charts/" + os.path.basename(pie_path)
    except Exception:
        pass
    try:
        recs = history.get_history_for_topic(topic)
        trend_path = charts.make_trend_chart(topic, recs)
        if trend_path:
            trend_url = "/charts/" + os.path.basename(trend_path)
    except Exception:
        pass

    return _render(topic=topic, result=result,
                   source_count=outcome["source_count"],
                   pie_url=pie_url, trend_url=trend_url)


def _compare_view(topic):
    """Xử lý chế độ so sánh nhiều chủ đề cho web."""
    topics = parse_topics(topic)
    outcome = run_comparison(topics, limit=50, save_history=True)
    if not outcome["ok"]:
        return _render(topic=topic, error=outcome["error"])

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
    except Exception:
        pass

    return _render(topic=topic, compare_items=items,
                   compare_topics=", ".join(topics),
                   compare_winner=winner, compare_url=compare_url)


@app.route("/charts/<path:filename>")
def serve_chart(filename):
    return send_from_directory(os.path.join(REPORTS_DIR, "charts"), filename)


if __name__ == "__main__":
    print("🌐 Web UI chạy tại http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
