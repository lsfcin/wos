# test_f8_footer_model.py — Lucas, live 2026-07-29: an opencode answer's footer named no model.
# Not a parser bug: opencode's JSONL never says which model ran. So the model is read from its own
# store after the turn, exactly as occupancy already is (b3/AD-24).
import json
from backend.providers import ocstore
from backend.base import AgentEvent
from backend.cli import CliBackend
from backend.providers.opencode import OpencodeBackend, parse_events

_MODEL = "nvidia/deepseek-ai/deepseek-v4-flash"
_CWD = "/a/project"


def _quiet_store(monkeypatch, model: str | None) -> None:
    """The store, stubbed: occupancy out of the way, and the model under test."""
    monkeypatch.setattr(ocstore, "last_turn", lambda sid: ("", None))
    monkeypatch.setattr(ocstore, "last_model", lambda sid: model)


def test_the_stream_itself_names_no_model_anywhere():
    """Checked against a real turn's JSONL: `text`, `step_start`, `tool_use` and `step_finish` all
    carry ids, cost and tokens — no model. This is why the footer had nothing to print."""
    line = json.dumps({"type": "step_finish", "sessionID": "ses_1", "part": {"cost": 0.001}})
    events = parse_events(line)
    assert events[0].model is None


def test_the_model_is_read_from_the_store_like_occupancy(monkeypatch):
    _quiet_store(monkeypatch, _MODEL)
    events = [AgentEvent(kind="result", session_id="ses_1")]
    OpencodeBackend()._attach_measured(events, _CWD)
    assert events[0].model == _MODEL


def test_a_model_the_stream_did_report_wins(monkeypatch):
    """claude names its model in the stream. The store is the FALLBACK, never an override — a
    turn that was told which model answered must not have it rewritten by a later store read."""
    _quiet_store(monkeypatch, _MODEL)
    events = [AgentEvent(kind="result", session_id="ses_1", model="sonnet")]
    OpencodeBackend()._attach_measured(events, _CWD)
    assert events[0].model == "sonnet"


def test_a_backend_that_cannot_say_leaves_it_empty():
    """The default hook knows nothing, and must not invent a name for the footer."""
    events = [AgentEvent(kind="result", session_id="ses_1")]
    CliBackend()._attach_measured(events, _CWD)
    assert events[0].model is None


def test_the_store_reads_provider_and_model_as_one_catalogue_id(monkeypatch):
    """`nvidia` + `deepseek-ai/deepseek-v4-flash` is one id everywhere else in the bot (the picker,
    the catalogue, the labels), so the footer must not be the one place it appears split."""
    message = ("msg_1", {"role": "assistant", "providerID": "nvidia",
                         "modelID": "deepseek-ai/deepseek-v4-flash"})
    monkeypatch.setattr(ocstore, "_last_assistant", lambda sid: message)
    assert ocstore.last_model("ses_1") == _MODEL
