# test_f8_ask_answer_shape.py — what an interview looks like in the chat, read on a phone.
#
# From Lucas reading a real one (2026-07-29): the option buttons were cut off ("Cada mensagem vira
# sessão nov…"), and once he answered, nothing in the chat said what he had answered.
import asyncio
from frontend.interview import ask, askserver
from frontend import phrases
from ..chatkit import Origin

_TOKEN = "abc123"
_OPTIONS = ["Cada mensagem vira sessão nova no opencode",
            "É a mesma sessão mas o histórico sumiu",
            "Não sei — descobre pra mim testando"]


def _call(token: str, question: str = "qual cor?", options: list | None = None) -> dict:
    args = {"question": question}
    if options is not None:
        args["options"] = options
    params = {"name": askserver.TOOL_NAME, "arguments": args}
    return {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": params}


async def _asked(token: str, **kw):
    pending = asyncio.create_task(askserver.handle_rpc(token, _call(token, **kw)))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    return pending


def _interview(answer_with, options=None, question="qual cor?"):
    """Ask, answer, and hand back the bubble as it ends up. `answer_with` takes the question id."""
    origin = Origin()
    ask.register(_TOKEN, origin)

    async def go():
        pending = await _asked(_TOKEN, question=question, options=options)
        bubble = origin.sent[0]
        qid = ask.question_of(bubble.message_id)
        answer_with(qid, bubble)
        await pending
        return bubble

    bubble = asyncio.run(go())
    ask.unregister(_TOKEN)
    return bubble


def _buttons(bubble):
    return [b for row in bubble.markup.inline_keyboard for b in row]


def test_the_options_are_written_out_in_the_question_not_squeezed_into_buttons():
    """Telegram truncates a button label and never wraps it (AD-5), so a phrase the agent wrote
    cannot live there. Every option's FULL text belongs in the message, where \\n works."""
    sent = []

    def answer_now(qid, bubble):
        sent.append(bubble.text)
        ask.answer(qid, _OPTIONS[0])

    _interview(answer_now, options=_OPTIONS)
    text = sent[0]
    for i, option in enumerate(_OPTIONS):
        assert f"{i + 1}. {option}" in text, "the option was cut or never listed"


def test_the_buttons_are_the_numbers_of_that_list():
    """The same shape /resume has used since it hit this exact wall: a numbered list in the text,
    numbers on the keys. A number never truncates, whatever the phone."""
    taps = []

    def answer_now(qid, bubble):
        taps.extend(_buttons(bubble))
        ask.answer(qid, _OPTIONS[0])

    _interview(answer_now, options=_OPTIONS)
    assert [b.text for b in taps] == ["1", "2", "3"]
    for i, button in enumerate(taps):
        assert button.callback_data.endswith(f":{i}"), "the tap must still carry its index"
        assert len(button.callback_data.encode()) <= 64


def test_a_tapped_option_answers_with_its_whole_text():
    """The number is what Lucas taps; the agent still receives the sentence it wrote."""
    def tap_second(qid, bubble):
        buttons = _buttons(bubble)
        ask.answer_tap(buttons[1].callback_data)

    bubble = _interview(tap_second, options=_OPTIONS)
    assert _OPTIONS[1] in bubble.text


def test_the_answer_is_written_under_the_question_in_italic():
    """Lucas, 2026-07-29: "answers are not registered". A question whose answer is not in the chat
    is unreadable a scroll later — you see what was asked and never what was decided."""
    def answer_now(qid, bubble):
        ask.answer(qid, "a segunda")

    bubble = _interview(answer_now)
    assert "<i>" in bubble.text and "a segunda" in bubble.text
    assert bubble.text.index("qual cor?") < bubble.text.index("a segunda"), "answer goes below"
    assert bubble.markup is None, "a settled question keeps no keyboard"


def test_an_unanswered_question_says_so_rather_than_quoting_the_agent():
    """The timeout text is an INSTRUCTION to the model ("siga com a hipótese mais razoável"), not
    something Lucas said, so it must never appear in the chat as if it were his answer."""
    def never(qid, bubble):
        ask.unregister(_TOKEN)

    bubble = _interview(never)
    assert ask.ENDED_TEXT not in bubble.text
    assert "sem resposta" in bubble.text


def test_the_reply_hint_goes_once_the_question_has_an_answer():
    """Caught by printing the bubbles rather than by an assertion: an answered question still said
    "responde essa mensagem", telling Lucas to do the thing he had just done."""
    def answer_now(qid, bubble):
        ask.answer(qid, "verde")

    bubble = _interview(answer_now)
    assert phrases.ASK_HINT not in bubble.text
    assert "verde" in bubble.text


def test_the_bubble_is_rewritten_from_what_was_SENT_not_from_telegrams_echo():
    """Telegram hands back the plain rendering of a message, never the HTML that was sent (AD-30).
    Rebuilding the bubble from `message.text` would silently drop the question's own markup."""
    def answer_now(qid, bubble):
        bubble.text = "PLAIN ECHO WITHOUT MARKUP"
        ask.answer(qid, "verde")

    bubble = _interview(answer_now, question="qual <b>cor</b>?")
    assert "PLAIN ECHO" not in bubble.text
    assert "verde" in bubble.text
