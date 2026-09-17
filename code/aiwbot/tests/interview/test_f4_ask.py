# test_f4_ask.py — F4 Stage 4: the broker. One asyncio.Future per question, the chat UX that
# resolves it (tap or reply), and the rule Lucas set — a wait always ends in TEXT the agent can
# act on, never in an MCP error, because an error aborts the turn and loses its work.
import asyncio
from frontend.interview import ask, askserver
from ..chatkit import Origin

_TOKEN = "abc123"


def _register(token: str = _TOKEN) -> Origin:
    origin = Origin()
    ask.register(token, origin)
    return origin


def _call(token: str, question: str = "qual cor?", options: list | None = None) -> dict:
    args = {"question": question}
    if options is not None:
        args["options"] = options
    params = {"name": askserver.TOOL_NAME, "arguments": args}
    return {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": params}


def _text_of(response: dict) -> str:
    content = response["result"]["content"]
    return content[0]["text"]


async def _asked(token: str, **kw):
    """Start the tool call and hand back the task once the question is on screen."""
    pending = asyncio.create_task(askserver.handle_rpc(token, _call(token, **kw)))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    return pending


def test_a_question_reaches_the_chat_and_its_answer_reaches_the_agent():
    origin = _register()

    async def go():
        pending = await _asked(_TOKEN)
        qid = ask.question_of(origin.sent[0].message_id)
        ask.answer(qid, "verde")
        return await pending

    response = asyncio.run(go())
    assert "qual cor?" in origin.sent[0].text
    assert _text_of(response) == "verde"
    ask.unregister(_TOKEN)


def test_the_options_the_agent_offers_become_buttons():
    """Revised 2026-07-29: the keys are the options' NUMBERS and the options themselves are listed
    in the message (a label truncates, a message wraps — AD-5). What is tested is unchanged: every
    option the agent offered is tappable, and no tap outgrows callback_data."""
    origin = _register()

    async def go():
        pending = await _asked(_TOKEN, options=["verde", "azul", "vermelho"])
        bubble = origin.sent[0]
        buttons = [b for row in bubble.markup.inline_keyboard for b in row]
        sent = bubble.text
        ask.answer(ask.question_of(bubble.message_id), "azul")
        await pending
        return buttons, sent

    buttons, sent = asyncio.run(go())
    assert [b.text for b in buttons] == ["1", "2", "3"]
    for i, option in enumerate(["verde", "azul", "vermelho"]):
        assert f"{i + 1}. {option}" in sent
    for button in buttons:
        assert len(button.callback_data.encode()) <= 64, "callback_data has 64 bytes, no more"
    ask.unregister(_TOKEN)


def test_a_tap_answers_with_the_option_it_carries():
    """The button says only WHICH option was tapped (callback_data is 64 bytes); the text it
    stands for is read back from the question the broker is still holding."""
    origin = _register()

    async def go():
        pending = await _asked(_TOKEN, options=["verde", "azul"])
        bubble = origin.sent[0]
        data = bubble.markup.inline_keyboard[0][1].callback_data
        ask.answer_tap(data)
        return await pending

    response = asyncio.run(go())
    assert _text_of(response) == "azul"
    ask.unregister(_TOKEN)


def test_a_free_text_reply_answers_the_question_it_replies_to():
    """The buttons are a shortcut, not the channel: the answer Lucas types (or dictates — voice
    arrives here as the same string) has to reach the waiting turn too."""
    origin = _register()

    async def go():
        pending = await _asked(_TOKEN, options=["verde", "azul"])
        qid = ask.question_of(origin.sent[0].message_id)
        ask.answer(qid, "nenhuma das duas, faz vermelho")
        return await pending

    response = asyncio.run(go())
    assert _text_of(response) == "nenhuma das duas, faz vermelho"
    ask.unregister(_TOKEN)


def test_an_unanswered_question_returns_text_not_an_mcp_error(monkeypatch):
    monkeypatch.setattr(ask, "WAIT_SECONDS", 0.01)
    _register()
    response = asyncio.run(askserver.handle_rpc(_TOKEN, _call(_TOKEN)))
    assert "error" not in response
    assert not response["result"].get("isError")
    assert _text_of(response)
    ask.unregister(_TOKEN)


def test_a_question_from_a_turn_that_ended_is_answered_in_text_too():
    """The turn's token is unregistered in a `finally`, so a late tool call finds nothing. It
    still may not raise — same reason as the timeout."""
    response = asyncio.run(askserver.handle_rpc("gone", _call("gone")))
    assert "error" not in response
    assert _text_of(response)


def test_the_turn_a_question_belongs_to_comes_from_the_url_not_the_payload():
    """MCP requests carry no turn id and turns run concurrently, so the ONLY correlation is the
    path the CLI was pointed at. Two live turns must not see each other's chat."""
    first = _register("t1")
    second = _register("t2")

    async def go():
        pending = await _asked("t2", question="pergunta B")
        ask.answer(ask.question_of(second.sent[0].message_id), "ok")
        await pending

    asyncio.run(go())
    assert first.sent == []
    assert "pergunta B" in second.sent[0].text
    ask.unregister("t1")
    ask.unregister("t2")


def test_a_second_answer_to_the_same_question_is_ignored():
    origin = _register()

    async def go():
        pending = await _asked(_TOKEN)
        qid = ask.question_of(origin.sent[0].message_id)
        first = ask.answer(qid, "verde")
        second = ask.answer(qid, "azul")
        return await pending, first, second

    response, first, second = asyncio.run(go())
    assert first is True
    assert second is False, "a stale tap must not resolve an answered question"
    assert _text_of(response) == "verde"
    ask.unregister(_TOKEN)


def test_the_keyboard_dies_with_the_question():
    """An answered question must stop offering its buttons, or a later tap resolves nothing and
    looks broken."""
    origin = _register()

    async def go():
        pending = await _asked(_TOKEN, options=["verde", "azul"])
        bubble = origin.sent[0]
        ask.answer(ask.question_of(bubble.message_id), "verde")
        await pending
        return bubble

    bubble = asyncio.run(go())
    assert bubble.markup is None
    ask.unregister(_TOKEN)


def test_ending_a_turn_releases_the_question_it_left_hanging():
    """The `finally` in runner unregisters the token. Anything still waiting on it has to be
    let go there and then — a future nobody will ever resolve is a leaked task per turn."""
    origin = _register()

    async def go():
        pending = await _asked(_TOKEN)
        ask.unregister(_TOKEN)
        return await asyncio.wait_for(pending, timeout=1)

    response = asyncio.run(go())
    assert _text_of(response)
    assert ask.question_of(origin.sent[0].message_id) is None
