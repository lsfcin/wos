# test_bot.py — free unit test: "bot"-prefix trigger routing logic.
from frontend.bot import _strip_bot_prefix


def test_strip_bot_prefix_space():
    assert _strip_bot_prefix("bot faz isso") == "faz isso"


def test_strip_bot_prefix_comma():
    assert _strip_bot_prefix("bot,faz isso") == "faz isso"


def test_strip_bot_prefix_case_insensitive():
    assert _strip_bot_prefix("BOT faz isso") == "faz isso"


def test_strip_bot_prefix_no_match():
    assert _strip_bot_prefix("robot faz isso") is None
    assert _strip_bot_prefix("lembrar de comprar pão") is None
