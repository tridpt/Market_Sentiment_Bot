"""Test cho logic phân quyền của bot.py (_parse_allowed_ids + _is_allowed).

bot.py yêu cầu TELEGRAM_BOT_TOKEN ngay lúc import, nên phải set env trước khi import.
Không kết nối Telegram; chỉ test logic thuần.
"""
import os
from types import SimpleNamespace

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token-for-ci")

import bot  # noqa: E402  (phải import sau khi đã set env token ở trên)


def _fake_update(user_id):
    """Tạo Update giả tối thiểu với effective_user.id."""
    if user_id is None:
        return SimpleNamespace(effective_user=None)
    return SimpleNamespace(effective_user=SimpleNamespace(id=user_id))


# ---------- _parse_allowed_ids ----------

def test_parse_allowed_ids_empty():
    assert bot._parse_allowed_ids("") == set()
    assert bot._parse_allowed_ids(None) == set()


def test_parse_allowed_ids_single():
    assert bot._parse_allowed_ids("12345") == {"12345"}


def test_parse_allowed_ids_multiple_with_spaces():
    assert bot._parse_allowed_ids("111, 222 , 333") == {"111", "222", "333"}


def test_parse_allowed_ids_ignores_blanks():
    assert bot._parse_allowed_ids("111,,  ,222") == {"111", "222"}


# ---------- _is_allowed ----------

def test_is_allowed_open_when_no_allowlist(monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_USER_IDS", set())
    assert bot._is_allowed(_fake_update(999)) is True


def test_is_allowed_permits_listed_user(monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_USER_IDS", {"123", "456"})
    assert bot._is_allowed(_fake_update(123)) is True


def test_is_allowed_blocks_unlisted_user(monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_USER_IDS", {"123"})
    assert bot._is_allowed(_fake_update(999)) is False


def test_is_allowed_blocks_when_no_user(monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_USER_IDS", {"123"})
    assert bot._is_allowed(_fake_update(None)) is False
