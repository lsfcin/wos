# test_parse_claude.py — free unit test: claude fixture -> normalized AgentEvents satisfy the contract.
import pathlib
from backend.providers.claude import parse_events, ClaudeBackend
from backend.base import check_contract, TurnOptions

_FIX = pathlib.Path(__file__).parent.parent / "fixtures" / "claude_pong.json"


def _events():
    raw = _FIX.read_text(encoding='utf-8')
    events = parse_events(raw)
    return events


def test_claude_has_text_and_result():
    events = _events()
    kinds = [e.kind for e in events]
    assert "text" in kinds
    assert "result" in kinds


def test_claude_text_and_session():
    events = _events()
    texts = [e for e in events if e.kind == "text"]
    first = texts[0]
    assert first.text == "PONG"
    assert first.session_id == "abc12345-6789-42ab-9cde-0123456789ab"


def test_claude_contract():
    events = _events()
    ok, reason = check_contract(events)
    assert ok, reason


def test_resume_is_single_lineage_no_fork():
    # AD-3 (revised): plain --resume keeps one lineage; --fork-session would mint a new id
    # per turn and pile up cumulative VSCode sessions. Lock the no-fork decision.
    backend = ClaudeBackend()
    args = backend.build_args("hi", "some-session-id", TurnOptions())
    assert "--resume" in args
    assert "--fork-session" not in args


def _perm_value(args):
    idx = args.index("--permission-mode")
    return args[idx + 1]


def test_build_args_build_mode_keeps_bypass():
    backend = ClaudeBackend()
    args = backend.build_args("hi", None, TurnOptions(mode="build"))
    assert _perm_value(args) == "bypassPermissions"


def test_build_args_plan_mode_sets_permission_plan():
    backend = ClaudeBackend()
    args = backend.build_args("hi", None, TurnOptions(mode="plan"))
    assert _perm_value(args) == "plan"


def test_build_args_new_session_sets_name():
    backend = ClaudeBackend()
    args = backend.build_args("hi", None, TurnOptions(title="my title"))
    idx = args.index("--name")
    assert args[idx + 1] == "my title"


def test_build_args_resume_omits_name():
    backend = ClaudeBackend()
    args = backend.build_args("hi", "sid-1", TurnOptions(title="my title"))
    assert "--name" not in args


def test_build_args_new_without_title_omits_name():
    backend = ClaudeBackend()
    args = backend.build_args("hi", None, TurnOptions())
    assert "--name" not in args


def test_list_sessions_reads_store(tmp_path, monkeypatch):
    import backend.providers.claude as C
    sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    line = '{"type":"last-prompt","lastPrompt":"olá mundo"}\n'
    (tmp_path / f"{sid}.jsonl").write_text(line, encoding='utf-8', newline='\n')
    monkeypatch.setattr(C, "_project_dir", lambda cwd: tmp_path)
    items = ClaudeBackend().list_sessions("/a/project")
    assert len(items) == 1
    assert items[0]["session_id"] == sid
    assert items[0]["title"] == "olá mundo"


def test_list_sessions_prefers_ai_title_over_prompt(tmp_path, monkeypatch):
    # AD-7: the latest `ai-title` is Claude Code's real picker title; the opening
    # prompt is only a fallback when no ai-title exists.
    import backend.providers.claude as C
    sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    prompt = '{"type":"last-prompt","lastPrompt":"## RESUME — ugly"}\n'
    title = '{"type":"ai-title","aiTitle":"Nice AI Title"}\n'
    (tmp_path / f"{sid}.jsonl").write_text(prompt + title, encoding='utf-8', newline='\n')
    monkeypatch.setattr(C, "_project_dir", lambda cwd: tmp_path)
    items = ClaudeBackend().list_sessions("/a/project")
    assert items[0]["title"] == "Nice AI Title"


def test_list_sessions_enriches_preview_and_model(tmp_path, monkeypatch):
    # Phase 3: the picker's 3-line entry needs a last-response preview + model, derived
    # from the transcript so VSCode sessions (no bot registry) also get them.
    import backend.providers.claude as C
    sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    title = '{"type":"ai-title","aiTitle":"Nice"}\n'
    asst = '{"type":"assistant","message":{"model":"claude-sonnet-5","content":[{"type":"text","text":"the last answer here"}]}}\n'
    (tmp_path / f"{sid}.jsonl").write_text(title + asst, encoding='utf-8', newline='\n')
    monkeypatch.setattr(C, "_project_dir", lambda cwd: tmp_path)
    items = ClaudeBackend().list_sessions("/a/project")
    assert items[0]["preview"] == "the last answer here"
    assert items[0]["model"] == "claude-sonnet-5"


def test_list_sessions_missing_dir_is_empty(tmp_path, monkeypatch):
    import backend.providers.claude as C
    monkeypatch.setattr(C, "_project_dir", lambda cwd: tmp_path / "nope")
    assert ClaudeBackend().list_sessions("/x") == []


def test_the_result_object_gives_the_window_but_never_the_occupancy():
    """b3: summing modelUsage's token fields measures SPEND. It aggregates every API request
    the invocation made, and a tool-using turn re-reads the whole context on each one — real
    transcripts sum to 6190% and 32533% of the window that way. The window is static metadata
    and stays; occupancy comes from the transcript via ClaudeBackend.occupancy."""
    import json
    from backend.providers.claude import parse_events
    obj = {"type": "result", "session_id": "s1", "result": "hi", "total_cost_usd": 0.1,
           "modelUsage": {"claude-opus-4-8": {"inputTokens": 2, "cacheReadInputTokens": 11036,
                                              "cacheCreationInputTokens": 13092,
                                              "contextWindow": 1000000}}}
    events = parse_events(json.dumps(obj))
    result = [e for e in events if e.kind == "result"][-1]
    assert result.context_used is None
    assert result.context_window == 1000000


def test_env_sets_entrypoint_so_sessions_are_natively_listed():
    # AD-8 (revised): the native picker hides sessions whose originating entrypoint is
    # sdk-cli; the value comes from this env var, not from the -p flag.
    env = ClaudeBackend().env(TurnOptions())
    assert env["CLAUDE_CODE_ENTRYPOINT"] == "claude-vscode"
