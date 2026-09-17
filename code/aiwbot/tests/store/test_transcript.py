# test_transcript.py — free unit test: tail-scan a claude .jsonl for title/preview/model.
from backend.providers import transcript


def _lines(*raw: str) -> list[str]:
    return list(raw)


def test_latest_ai_title_wins_over_earlier():
    lines = _lines(
        '{"type":"ai-title","aiTitle":"first title"}',
        '{"type":"assistant","message":{"content":[{"type":"text","text":"hi"}]}}',
        '{"type":"ai-title","aiTitle":"second title"}',
        '{"type":"last-prompt","lastPrompt":"trailing prompt"}',
    )
    assert transcript.latest_ai_title(lines) == "second title"


def test_latest_ai_title_empty_when_absent():
    lines = _lines('{"type":"last-prompt","lastPrompt":"only a prompt"}')
    assert transcript.latest_ai_title(lines) == ""


def test_last_response_text_takes_last_assistant_text_block():
    lines = _lines(
        '{"type":"assistant","message":{"content":[{"type":"text","text":"old"}]}}',
        '{"type":"user","message":{"content":"noise"}}',
        '{"type":"assistant","message":{"content":[{"type":"tool_use"},{"type":"text","text":"new answer"}]}}',
    )
    assert transcript.last_response_text(lines) == "new answer"


def test_last_response_text_empty_when_no_assistant():
    lines = _lines('{"type":"user","message":{"content":"hi"}}')
    assert transcript.last_response_text(lines) == ""


def test_last_model_reads_assistant_message_model():
    lines = _lines('{"type":"assistant","message":{"model":"claude-sonnet-5","content":[]}}')
    assert transcript.last_model(lines) == "claude-sonnet-5"


def test_tail_lines_reads_bounded_tail(tmp_path):
    path = tmp_path / "s.jsonl"
    body = "\n".join(f'{{"type":"noise","i":{i}}}' for i in range(1000))
    path.write_text(body + '\n{"type":"ai-title","aiTitle":"tail title"}\n', encoding='utf-8', newline='\n')
    lines = transcript.tail_lines(path, kb=1)
    assert transcript.latest_ai_title(lines) == "tail title"
