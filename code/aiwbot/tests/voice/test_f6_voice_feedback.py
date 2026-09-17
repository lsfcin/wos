# test_f6_voice_feedback.py — a voice note says something back before it has been transcribed
# (Lucas, 2026-07-28: "demora para aparecer qualquer feedback"). The download plus whisper take
# seconds, and silence for that long reads as being ignored.
import asyncio
from frontend import bot
from frontend.turn import runner
from ..chatkit import FakeMsg, FakeReplyAnchor


def test_a_voice_note_is_acknowledged_before_the_transcription_runs(store, monkeypatch):
    """Whisper takes seconds and the download takes more, so an audio turn used to sit silent
    long enough to read as "the bot ignored me". The status goes out FIRST, and it names what is
    happening rather than saying ok."""
    order = []

    class _Msg:
        reply_to_message = None
        forward_origin = None

        async def reply_text(self, text, parse_mode=None, do_quote=False, reply_markup=None):
            order.append(("said", text))
            return FakeReplyAnchor(7)

    async def fake_save(file_id, context, suffix):
        order.append(("downloaded", None))
        return "/tmp/x.ogg"

    monkeypatch.setattr(bot.inbox, "save_media", fake_save)
    monkeypatch.setattr(bot.stt, "transcribe", lambda p: order.append(("transcribed", None)) or "bot faz isso")

    async def fake_route(msg, text, context, *, spoken=False, working=None):
        order.append(("routed", working))

    monkeypatch.setattr(bot, "_route_text", fake_route)
    msg = _Msg()
    msg.voice = type("V", (), {"file_id": "f"})()
    asyncio.run(bot._handle_voice(msg, None))

    steps = [step for step, _ in order]
    assert steps == ["said", "downloaded", "transcribed", "routed"]
    assert order[-1][1] is not None, "the status bubble must be handed to the turn, not abandoned"


def test_the_status_bubble_becomes_the_turns_working_message(store, monkeypatch):
    """One bubble, morphed — not a status followed by a second "trabalhando…" message."""
    edited = []

    async def fake_edit(message, text, markup=None):
        edited.append(text)
        return True

    monkeypatch.setattr(runner.reply, "edit_text", fake_edit)

    async def fake_safe_reply(msg, text, reply_markup=None):
        raise AssertionError("a second status bubble was sent")

    monkeypatch.setattr(runner.reply, "safe_reply", fake_safe_reply)
    existing = FakeReplyAnchor(7)
    result = asyncio.run(runner._working(FakeMsg(), existing))
    assert result is existing
    assert edited, "the status was left saying it was still transcribing"


# --- a transient failure is retried, not reported (Lucas, 2026-07-29) -------------------------

def _turn(monkeypatch, failures, streamed_text=""):
    """Run one turn whose dispatch fails `failures` times, then succeeds. Returns (attempts, said)."""
    said = []
    attempts = []

    class _Result:
        text = "pronto"
        session_id = "s1"
        cost_usd = None
        model = "sonnet"
        context_used = None
        context_window = None

    async def fake_turn(prompt, **kw):
        attempts.append(prompt)
        if len(attempts) <= len(failures):
            raise runner.dispatch.DispatchError(failures[len(attempts) - 1])
        return _Result()

    async def fake_edit(message, text, markup=None):
        said.append(text)
        return True

    async def fake_deliver(working, msg, text, reply_markup=None, lead=""):
        said.append(text)
        return []

    async def no_sleep(seconds):
        return None

    monkeypatch.setattr(runner.dispatch, "turn", fake_turn)
    monkeypatch.setattr(runner.reply, "edit_text", fake_edit)
    monkeypatch.setattr(runner.reply, "deliver", fake_deliver)
    monkeypatch.setattr(runner.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(runner.helpers, "persist_turn", lambda *a, **kw: None)
    monkeypatch.setattr(runner.msgmap, "remember_reply", lambda *a: None)
    asyncio.run(runner.run_and_deliver(FakeMsg(), FakeReplyAnchor(7), "faz isso", session_id=None,
                                        backend_name="claude", title=None, scope="s1"))
    return attempts, said


def test_an_overloaded_provider_is_retried_by_itself(store, monkeypatch):
    """A 529 is about the moment, not the request. Lucas is usually not watching, so letting one
    through costs him the whole task rather than a few seconds."""
    attempts, said = _turn(monkeypatch, ["API Error: 529 Overloaded"])
    assert len(attempts) == 2, "the turn was not tried again"
    assert any("sobrecarga" in text or "sobrecarregada" in text for text in said)


def test_a_failure_about_the_request_itself_is_not_retried(store, monkeypatch):
    """No session, a bad prompt: it would fail identically every time, so retrying only delays
    telling him."""
    attempts, said = _turn(monkeypatch, ["no conversation found"] * 3)
    assert len(attempts) == 1


def test_retrying_gives_up_and_says_so(store, monkeypatch):
    attempts, said = _turn(monkeypatch, ["529 overloaded"] * 9)
    assert len(attempts) == runner.RETRIES + 1
    assert any("erro" in text or "falhou" in text or "quebrou" in text for text in said)


def test_the_status_bubble_shows_the_transcript_before_the_answer_exists(store, monkeypatch):
    """Lucas, 2026-07-29: once the transcription is done it can already be shown — seeing what was
    heard should not wait for the reply. So the bubble that said "transcrevendo…" becomes the
    quoted transcript plus "trabalhando…", and the painter keeps writing into that same bubble."""
    from frontend.stream import answer
    edited = []

    async def fake_edit(message, text, markup=None):
        edited.append(text)
        return True

    monkeypatch.setattr(runner.reply, "edit_text", fake_edit)
    lead = answer.quote("me explica o ciclo da água")
    asyncio.run(runner._working(FakeMsg(), FakeReplyAnchor(7), lead))
    assert edited, "the status never changed"
    assert edited[0].startswith(lead)
    assert "ciclo da água" in edited[0]
