# 📝 Changelog

Mọi thay đổi đáng chú ý của dự án được ghi lại ở đây.

Định dạng theo [Keep a Changelog](https://keepachangelog.com/),
và dự án tuân theo [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-06-15

Phiên bản hoàn chỉnh đầu tiên — đầy đủ 3 giao diện, đa nguồn dữ liệu, biểu đồ, test và CI.

### Added
- **3 giao diện**: CLI (`main.py`), Telegram bot (`bot.py`), Web UI Flask (`webapp.py`).
- **Đa nguồn dữ liệu**: Hacker News + Google News (tiếng Anh & tiếng Việt); tùy chọn thêm YouTube + Reddit (OAuth) khi có credentials.
- **Phân tích bằng Google Gemini 2.5 Flash** trả về JSON có cấu trúc (tỷ lệ %, top khen/chê, kết luận), có retry khi máy chủ quá tải.
- **So sánh nhiều sản phẩm** — nhập `iPhone vs Samsung` (hỗ trợ `vs`/`versus`/`với`/dấu phẩy), tự nhận diện trên cả 3 giao diện.
- **Biểu đồ** (matplotlib): tròn (tỷ lệ), đường (xu hướng theo thời gian), cột (so sánh).
- **Xuất báo cáo** ra Markdown + JSON có timestamp.
- **Theo dõi xu hướng** — lưu lịch sử phân tích vào `data/history.json`.
- **Cache trong bộ nhớ** — quét lại cùng chủ đề trong 10 phút trả kết quả cũ, tiết kiệm quota Gemini.
- **44 unit test** (pytest, dùng mock — không gọi API thật).
- **GitHub Actions CI** — tự chạy test trên Python 3.11/3.12/3.13 mỗi lần push/PR.
- **Tài liệu**: README chuẩn portfolio (kèm ảnh demo), bộ docs kỹ thuật (`ARCHITECTURE`, `API_REFERENCE`, `USAGE`, `CONTRIBUTING`), issue/PR templates, LICENSE (MIT).

### Changed
- Đổi nguồn dữ liệu từ Reddit `.json` (bị chặn 403) sang Hacker News + Google News.
- Khởi tạo Gemini client kiểu **lazy** để import module an toàn khi thiếu `GEMINI_API_KEY` (cần cho CI).
- Tách phụ thuộc dev (pytest, playwright) sang `requirements-dev.txt`.

### Fixed
- Lỗi `UnicodeEncodeError` khi pipe output có emoji trên Windows (cp1252) — ép stdout/stderr về UTF-8.

[1.0.0]: https://github.com/tridpt/Market_Sentiment_Bot/releases/tag/v1.0.0
