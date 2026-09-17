# test_reply_voice.py — free unit test: reply.send_voice (C5), mirrors safe_reply's Telegram-error
# tolerance so a rejected voice send degrades to None rather than raising.
import asyncio
from telegram.error import TelegramError
from frontend import reply


class FakeMsg:
    def __init__(self):
        self.sent = None

    async def reply_voice(self, voice, **kw):
        self.sent = voice
        return "SENT"


class FailingMsg:
    async def reply_voice(self, voice, **kw):
        raise TelegramError("boom")


def test_send_voice_sends_the_ogg_bytes():
    msg = FakeMsg()
    result = asyncio.run(reply.send_voice(msg, b"OGGDATA"))
    assert result == "SENT"
    assert msg.sent == b"OGGDATA"


def test_send_voice_degrades_to_none_on_telegram_error():
    result = asyncio.run(reply.send_voice(FailingMsg(), b"OGGDATA"))
    assert result is None
