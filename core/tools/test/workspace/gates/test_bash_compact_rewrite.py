# T0 the multi-line rtk shim: it must reach lines 2+, and must never reshape shell it cannot read.
#
# rtk parses the first line of a Bash payload and nothing else, so `cd x` + newline + `git status`
# rewrote nothing at all — 23.4% of this workspace's Bash calls open with `cd`. The shim splits the
# payload and rewrites each line; the risk it introduces is the opposite of the bug it fixes, so the
# bail cases below matter more than the rewrite ones. Failing to compact costs tokens; corrupting a
# command costs correctness.
#
# Every case runs against a stub `rtk` on PATH, so the suite stays hermetic and asserts the shim's
# own logic rather than the binary's rewrite table.
import json
import os
import shutil
import subprocess

import pytest

from conftest import WORKSPACE_ROOT
from platform_law import install_command, interpreter

SHIM = WORKSPACE_ROOT / 'core/hooks/compact/bash-compact-rewrite.py'

# Mimics the real binary: reads the FIRST line only, and declines when that line is not its business.
# No shebang: install_command owns how a command becomes runnable, which is not the same mechanism
# on every machine, and the stub has no business knowing which one it got.
STUB = '''import json, sys
HANDLED = {'git', 'ls', 'grep'}
payload = json.load(sys.stdin)
command = payload.get('tool_input', {}).get('command', '')
lines = command.split('\\n')
if lines and lines[0].strip().split(' ')[0] in HANDLED:
    lines[0] = 'rtk ' + lines[0]
    out = dict(payload.get('tool_input', {}))
    out['command'] = '\\n'.join(lines)
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
                                             'permissionDecisionReason': 'stub',
                                             'updatedInput': out}}))
'''


def _path_without_rtk() -> str:
	"""The real PATH minus every directory that already ships an rtk, so the stub is the only one."""
	kept = [d for d in os.environ.get('PATH', '').split(os.pathsep)
	        if d and not os.access(os.path.join(d, 'rtk'), os.X_OK)]
	return os.pathsep.join(kept)


@pytest.fixture
def rtk_path(tmp_path):
	"""A PATH whose only `rtk` is the stub above."""
	install_command(tmp_path, 'rtk', STUB)
	return f'{tmp_path}{os.pathsep}{_path_without_rtk()}'


def _run(command: str, path: str, tool: str = 'Bash', counter: str = '') -> str:
	payload = {'session_id': 'test', 'cwd': str(WORKSPACE_ROOT), 'tool_name': tool,
	           'tool_input': {'command': command, 'description': 'd'}}
	# PATH is overridden, the rest of the environment is INHERITED. Replacing it outright is a
	# POSIX habit: on Windows a bare env has no PATHEXT (so `which` cannot tell what is runnable)
	# and no COMSPEC (so nothing can launch what it finds), and the shim then reports rtk absent.
	env = {**os.environ, 'PATH': path}
	if counter:
		env['RTK_COMPACT_DIR'] = counter
	done = subprocess.run([interpreter(), str(SHIM)], input=json.dumps(payload),
	                      capture_output=True, text=True, env=env, encoding='utf-8')
	assert done.returncode == 0, done.stderr
	return done.stdout.strip()


def _rewritten(command: str, path: str) -> str | None:
	"""The command the shim would actually run, or None when it asked for no change."""
	out = _run(command, path)
	if not out:
		return None
	return json.loads(out)['hookSpecificOutput']['updatedInput']['command']


def test_a_command_stranded_after_cd_is_reached(rtk_path) -> None:
	"""The measured bug: rtk spends its one shot on the `cd` and drops everything after it."""
	assert _rewritten('cd /tmp\ngit status', rtk_path) == 'cd /tmp\nrtk git status'


def test_every_line_is_rewritten_not_just_the_first(rtk_path) -> None:
	"""The stub alone would leave line 2 raw; the shim is the whole reason it does not."""
	assert _rewritten('git status\nls -la', rtk_path) == 'rtk git status\nrtk ls -la'


@pytest.mark.parametrize('command', [
	"python3 - <<'PY'\nprint(1)\nPY",          # heredoc: lines 2+ are data, not commands
	'cd /tmp\nfor f in a b; do echo $f; done',  # block keyword
	'cd /tmp\ngrep -r foo . |\n  head -5',      # a line that continues onto the next
	"git commit -m 'first line\nls is prose here'",  # a quoted string spanning lines
])
def test_shell_it_cannot_read_is_left_exactly_as_written(command, rtk_path) -> None:
	"""The bail is the safe direction: hand the payload to rtk untouched and pass its verdict through."""
	assert _rewritten(command, rtk_path) == _rewritten_by_stub_alone(command, rtk_path)


def _rewritten_by_stub_alone(command: str, path: str) -> str | None:
	payload = {'tool_name': 'Bash', 'tool_input': {'command': command, 'description': 'd'}}
	env = {**os.environ, 'PATH': path}
	done = subprocess.run([shutil.which('rtk', path=path), 'hook', 'claude'],
	                      input=json.dumps(payload),
	                      capture_output=True, text=True, env=env, encoding='utf-8')
	if not done.stdout.strip():
		return None
	return json.loads(done.stdout)['hookSpecificOutput']['updatedInput']['command']


def test_a_single_line_is_rtk_s_own_business(rtk_path) -> None:
	"""The shim adds nothing on the shape rtk already handles; it must not double-prefix."""
	assert _rewritten('git status', rtk_path) == 'rtk git status'


def test_a_payload_with_nothing_to_gain_stays_silent(rtk_path) -> None:
	"""No rewrite means no `updatedInput` at all, so the harness is never handed a no-op."""
	assert _run('echo one\necho two', rtk_path) == ''


def test_a_non_bash_tool_is_not_touched(rtk_path) -> None:
	assert _run('git status\nls -la', rtk_path, tool='Read') == ''


def test_a_missing_rtk_fails_open() -> None:
	"""Compaction is an optimisation; without the binary the command must still run as written."""
	assert _run('cd /tmp\ngit status', _path_without_rtk()) == ''


# ── The adoption counter. It exists because the multi-line bug was invisible for weeks: the
#    configuration read as correct, and nothing on disk disagreed. These assert the one property
#    that makes it an instrument — a shim reaching nothing must be distinguishable from a shim
#    doing its job, which is exactly what `rtk gain` cannot tell you.

def _verdicts(counter, session: str = 'test') -> list[str]:
	log = counter / f'claude_rtk_compact_{session}.tsv'
	if not log.exists():
		return []
	return [line.split('\t')[0] for line in log.read_text(encoding='utf-8').splitlines()]


def test_reaching_a_stranded_command_is_counted(rtk_path, tmp_path) -> None:
	"""The shape the bug hid in. It must leave a row saying it was rewritten, not merely run."""
	counter = tmp_path / 'counter'
	counter.mkdir()
	_run('cd /tmp\ngit status', rtk_path, counter=str(counter))
	assert _verdicts(counter) == ['split-rewrote']


def test_a_payload_with_nothing_to_gain_is_counted_as_a_miss(rtk_path, tmp_path) -> None:
	"""A no-op must still leave a row. Counting only successes is how 0% adoption reads as silence."""
	counter = tmp_path / 'counter'
	counter.mkdir()
	_run('echo one\necho two', rtk_path, counter=str(counter))
	assert _verdicts(counter) == ['split-noop']


def test_a_missing_rtk_is_counted_as_such(tmp_path) -> None:
	"""`no-rtk` must not be filed as a miss: an uninstalled binary and an idle shim are
	different failures, and the roundup's percentage is unreadable if they collapse."""
	counter = tmp_path / 'counter'
	counter.mkdir()
	_run('cd /tmp\ngit status', _path_without_rtk(), counter=str(counter))
	assert _verdicts(counter) == ['no-rtk']


def test_counting_never_breaks_the_command_being_counted(rtk_path, tmp_path) -> None:
	"""An unwritable counter is a lost measurement, never a lost command."""
	counter = tmp_path / 'nonexistent'
	assert _rewritten_with_counter('cd /tmp\ngit status', rtk_path, str(counter)) == \
	       'cd /tmp\nrtk git status'


def _rewritten_with_counter(command: str, path: str, counter: str) -> str | None:
	out = _run(command, path, counter=counter)
	if not out:
		return None
	return json.loads(out)['hookSpecificOutput']['updatedInput']['command']
