# T0 context meter (core/SPECS.md § AD-09): the session-size signal that decides when to hand off.
# Zero-token, runs in verify-fast.
#
# Two things are worth guarding here. The thresholds must come from limits.env, so the
# numbers can be re-tuned without touching the checker — the same rule that already binds
# every other checker to its law file. And the meter must announce each threshold exactly
# once: a warning that repeats every turn is one Lucas learns to skip, which costs the
# tokens without buying the decision.
import importlib.util
import json
import re

from conftest import WORKSPACE_ROOT

def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, WORKSPACE_ROOT / path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


context_meter = _module('context_meter', 'core/hooks/session/context-meter.py')
# The tail scan moved to transcript.py when the statusline became its second reader
# (2026-09-15). The meter still owns the thresholds and the once-per-crossing rule; reading
# the transcript is now a question with one answer for both, so it is asked of its own module.
transcript = _module('transcript', 'core/hooks/session/transcript.py')

LIMITS = WORKSPACE_ROOT / 'core/hooks/limits.env'


def _turn(ctx, sidechain=False, role='assistant'):
    return json.dumps({
        'type': role,
        'isSidechain': sidechain,
        'message': {'usage': {
            'input_tokens': 2,
            'cache_read_input_tokens': ctx - 2,
            'cache_creation_input_tokens': 0,
        }},
    })


def _transcript(tmp_path, lines):
    path = tmp_path / 'session.jsonl'
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    return str(path)


def test_thresholds_come_from_limits_env():
    """The meter reads the numbers; it must not carry a copy of them."""
    limits = context_meter.load_limits()
    assert limits['CTX_WARN'] < limits['CTX_LOUD']
    source = (WORKSPACE_ROOT / 'core/hooks/session/context-meter.py').read_text(encoding='utf-8')
    for value in (limits['CTX_WARN'], limits['CTX_LOUD']):
        assert str(value) not in source, (
            f'{value} is hardcoded in context-meter.py — it belongs only in limits.env')


def test_declared_in_limits_env():
    text = LIMITS.read_text(encoding='utf-8')
    assert 'CTX_WARN=' in text and 'CTX_LOUD=' in text


def test_reads_the_most_recent_turn(tmp_path):
    path = _transcript(tmp_path, [_turn(40_000), _turn(310_000)])
    assert transcript.last_context(path) == 310_000


def test_subagent_turns_are_not_the_session(tmp_path):
    """A sidechain turn carries its own small context — it is not what the session holds."""
    path = _transcript(tmp_path, [_turn(310_000), _turn(9_000, sidechain=True)])
    assert transcript.last_context(path) == 310_000


def test_missing_or_unreadable_transcript_is_silent(tmp_path):
    assert transcript.last_context(str(tmp_path / 'absent.jsonl')) == 0
    garbage = tmp_path / 'garbage.jsonl'
    garbage.write_text('not json at all\n{"usage": broken\n', encoding='utf-8', newline='\n')
    assert transcript.last_context(str(garbage)) == 0


def test_each_threshold_announces_once(tmp_path, monkeypatch):
    state = tmp_path / 'state.txt'
    monkeypatch.setattr(context_meter, 'state_file', lambda _sid: str(state))
    limits = context_meter.load_limits()
    warn, loud = limits['CTX_WARN'], limits['CTX_LOUD']

    assert context_meter.announced('s') == 0
    context_meter.mark('s', warn)
    assert context_meter.announced('s') == warn
    # Still inside the warn band on a later turn — already said, stay quiet.
    assert warn <= context_meter.announced('s')
    # Crossing the louder mark is new information, so it speaks again.
    assert loud > context_meter.announced('s')


def test_the_loud_message_names_the_way_out(tmp_path):
    limits = context_meter.load_limits()
    text = context_meter.message(300_000, limits['CTX_LOUD'], limits['CTX_LOUD'])
    assert '/roundup' in text and '300k' in text


def test_both_messages_name_roundup_and_nothing_else():
    """One command, always the same one. /roundup Phase 6 already runs /handoff, so naming
    both ran the ritual twice; naming the artifact, or saying 'hand off' in the abstract,
    invites the session to improvise a close instead of using the one we built."""
    limits = context_meter.load_limits()
    for crossed in (limits['CTX_WARN'], limits['CTX_LOUD']):
        text = context_meter.message(crossed + 4_000, crossed, limits['CTX_LOUD'])
        assert '/roundup' in text
        assert '/handoff' not in text and 'handoff.md' not in text
        assert text.count('/') == 1, f'more than one command named: {text}'


def test_the_warn_message_stays_ignorable():
    """The first nudge exists to be ignorable — see brain/SPECS.md § Rationale. It may name
    /roundup, but it must also say, in as many words, that finishing instead is fine."""
    limits = context_meter.load_limits()
    text = context_meter.message(limits['CTX_WARN'] + 4_000, limits['CTX_WARN'], limits['CTX_LOUD'])
    assert 'stopping point' in text and 'ignore this' in text


def test_both_messages_stay_short_and_jargon_free():
    """These are read by an agent mid-thread, so they are two lines of plain words or they get
    skimmed. 'band' and 'turns' are cost-table vocabulary and mean nothing at the prompt."""
    limits = context_meter.load_limits()
    for ctx, crossed in ((limits['CTX_WARN'] + 4_000, limits['CTX_WARN']),
                         (limits['CTX_LOUD'] + 13_000, limits['CTX_LOUD'])):
        text = context_meter.message(ctx, crossed, limits['CTX_LOUD'])
        assert len(text) <= 240, f'{len(text)} chars — trim it, this interrupts a live thread'
        assert 'band' not in text
        assert text.startswith('CONTEXT WINDOW:'), 'say which window, and that it is *used*'


def test_the_thresholds_bracket_the_measured_climb():
    """WARN marks where cost starts bending, LOUD where it plateaus — both from the curve in
    limits.env, not taste. Guards against re-tuning one and leaving the other stranded."""
    limits = context_meter.load_limits()
    assert limits['CTX_WARN'] < limits['CTX_LOUD']
    text = LIMITS.read_text(encoding='utf-8')
    assert '/turn' in text, 'limits.env must keep the measured curve that justifies the numbers'
    assert 'core/tools/wos/session/usage' in text, 'the curve must name the command that reproduces it'


def test_the_handoff_artifact_is_not_an_uppercase_type():
    """The path lives in exactly one place — /handoff, which writes it. core/SCHEMA.md § types
    is a closed allowlist, so the resume prompt must be an instance: HANDOFF.md is off that
    allowlist, which is why it never existed despite a .gitignore line inherited for it."""
    skill = (WORKSPACE_ROOT / 'core/skills/handoff.md').read_text(encoding='utf-8')
    written = re.findall(r'outputs/[\w.-]+\.md', skill)
    assert written, 'core/skills/handoff.md no longer names the file it writes'
    for path in set(written):
        name = path.rsplit('/', 1)[-1]
        assert name == name.lower(), f'{name} reads as a type — types are allowlisted in SCHEMA.md'


def test_the_meter_never_spawns_a_session():
    """Decided 2026-08-13 (core/SPECS.md § AD-09): a successor cannot take the terminal, so none
    is spawned.

    THE RULE IS ABOUT A SESSION, NOT ABOUT A PROCESS (2026-09-15). This used to forbid the word
    `subprocess` anywhere in the source, which stopped being the same question the moment the
    meter started reaching the out-of-band channel through notify.py — the ban held on the
    literal text while a process was being spawned one import away. A test that passes by
    indirection is worse than no test. So the session spawns are named, and the one process the
    meter may reach is named with them.
    """
    source = (WORKSPACE_ROOT / 'core/hooks/session/context-meter.py').read_text(encoding='utf-8')
    for forbidden in ('--bg', 'claude -p', 'os.system', 'Popen'):
        assert forbidden not in source, f'{forbidden} in a hook that must never take the terminal'
    assert 'subprocess' not in source, (
        'the meter reaches a process only through notify.py, which owns the timeout and the '
        'failure stance — spawning one here would be a second copy of both')
