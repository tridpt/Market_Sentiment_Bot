"""Telegram Bot: nhắn tên sản phẩm -> nhận báo cáo cảm xúc + biểu đồ ngay trong chat.

Lệnh hỗ trợ:
  /start            - giới thiệu
  /history          - liệt kê các chủ đề đã phân tích
  /trend <chủ đề>   - xem biểu đồ xu hướng theo thời gian của một chủ đề
  <văn bản bất kỳ>  - phân tích cảm xúc cho chủ đề đó
"""
import os
import sys
import asyncio

# Ép stdout/stderr về UTF-8 để log emoji không crash trên Windows (cp1252)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from engine import run_analysis
from reporter import format_telegram
from charts import make_pie_chart, make_trend_chart
import history

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID")

if not TOKEN:
    raise ValueError("Chưa có TELEGRAM_BOT_TOKEN trong .env")


def _is_allowed(update: Update) -> bool:
    """Chỉ cho phép user_id được cấu hình trong .env (nếu có cấu hình)."""
    if not ALLOWED_USER_ID:
        return True  # không giới hạn nếu chưa cấu hình
    user = update.effective_user
    return user is not None and str(user.id) == str(ALLOWED_USER_ID)


async def _deny(update: Update):
    await update.message.reply_text("⛔ Bạn không có quyền dùng bot này.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_allowed(update):
        return await _deny(update)
    await update.message.reply_text(
        "🚀 <b>Bot Phân Tích Tâm Lý Thị Trường</b>\n\n"
        "Nhắn cho mình tên một sản phẩm/chủ đề (VD: <i>iPhone 15</i>, <i>VinFast</i>), "
        "mình sẽ cào tin tức + diễn đàn rồi nhờ AI tổng hợp dư luận cho bạn.\n\n"
        "Lệnh khác:\n"
        "• /history – các chủ đề đã phân tích\n"
        "• /trend &lt;chủ đề&gt; – xem xu hướng theo thời gian",
        parse_mode="HTML",
    )


async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_allowed(update):
        return await _deny(update)
    topics = history.list_topics()
    if not topics:
        await update.message.reply_text("Chưa có lịch sử phân tích nào.")
        return
    lines = ["📚 <b>Các chủ đề đã phân tích:</b>\n"]
    for t, c in sorted(topics.items(), key=lambda x: -x[1]):
        lines.append(f"• {t} ({c} lần)")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def trend_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_allowed(update):
        return await _deny(update)
    topic = " ".join(context.args).strip()
    if not topic:
        await update.message.reply_text("Cú pháp: /trend <chủ đề>")
        return
    records = history.get_history_for_topic(topic)
    if len(records) < 2:
        await update.message.reply_text(
            f"Chủ đề '{topic}' cần ít nhất 2 lần phân tích để vẽ xu hướng "
            f"(hiện có {len(records)})."
        )
        return
    chart = await asyncio.to_thread(make_trend_chart, topic, records)
    if chart:
        with open(chart, "rb") as f:
            await update.message.reply_photo(photo=f, caption=f"📉 Xu hướng cảm xúc: {topic}")


async def analyze_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_allowed(update):
        return await _deny(update)
    topic = (update.message.text or "").strip()
    if not topic:
        return

    await update.message.reply_text(f"⛏️ Đang đào dữ liệu & phân tích '{topic}'... chờ chút nhé.")
    await update.message.chat.send_action(ChatAction.TYPING)

    # Chạy pipeline (blocking) trong thread để không khóa event loop
    res = await asyncio.to_thread(run_analysis, topic, 50, True)

    if not res["ok"]:
        await update.message.reply_text(f"❌ {res['error']}")
        return

    result = res["result"]
    await update.message.reply_text(
        format_telegram(topic, result) + f"\n\n<i>Nguồn: {res['source_count']} đoạn dữ liệu</i>",
        parse_mode="HTML",
    )

    # Gửi kèm biểu đồ tròn
    try:
        pie = await asyncio.to_thread(make_pie_chart, topic, result)
        with open(pie, "rb") as f:
            await update.message.reply_photo(photo=f, caption=f"📊 Tỷ lệ dư luận: {topic}")
    except Exception:
        pass


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CommandHandler("trend", trend_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_msg))

    print("🤖 Bot đang chạy... (Ctrl+C để dừng)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
