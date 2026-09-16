# b20260904 regression — a write performed inside an interpreted heredoc body is seen.
#
# `"$(sh core/run --python)" - <<'PYEOF'` running a body that calls Path('ISSUES.md').write_text(...)
# fired no PreToolUse: Edit|Write hook at all: not the size gate, not the first-line-comment check,
# not issues-gate.py. Used that way on 2026-09-04 to delete two bug sections. The gate spotted a
# write by SHELL syntax only, and stated its stdin exclusion as "writes nothing" — a claim about
# redirects being read as a claim about the process.
#
# The exclusion stays, and these cases are what makes that safe: a body is read only when it BOTH
# calls a write verb and names a path git tracks. The silence cases carry the weight here, exactly
# as they do in test_heredoc_gate.py next door, whose `run` this reuses.
import pytest

from test_heredoc_gate import run

# Tracked, at the repo root, and the file the incident actually wrote. Relative on purpose: the
# gate resolves against the payload's cwd, so a hard-coded absolute path would prove nothing here.
TRACKED = 'ISSUES.md'
INTERPRETER = '"$(sh core/run --python)" - '


def _heredoc(body: str, opener: str = INTERPRETER) -> str:
	return f"{opener}<<'PYEOF'\n{body}\nPYEOF"


def test_a_body_that_writes_a_tracked_file_is_named():
	"""The incident itself: the write the file gates would have seen had it gone through Edit."""
	command = _heredoc(f"from pathlib import Path\nPath('{TRACKED}').write_text('x')")
	assert 'UNGATED WRITE' in run(command)


@pytest.mark.parametrize('body', [
	f"from pathlib import Path\nprint(Path('{TRACKED}').read_text().count('##'))",
	"from pathlib import Path\nPath('/tmp/scratch.json').write_text('{}')",
	"import json\nprint(json.dumps({'rows': 3}))",
])
def test_a_body_that_fails_either_condition_stays_silent(body):
	"""Reading a tracked file, or writing an untracked one, is the 44% the exclusion was bought for.

	Both conditions must meet. A verb alone fires on every script that saves a scratch file; a
	tracked path alone fires on every script that merely reads one — and either would be the noise
	that gets a warn-only gate switched off."""
	assert run(_heredoc(body)) == ''


def test_a_body_is_read_only_when_its_opener_fed_an_interpreter():
	"""`cat > /tmp/x <<'EOF'` carries plain text. Parsing every body would undo the exclusion."""
	command = _heredoc(f"Path('{TRACKED}').write_text('x')", opener='cat > /tmp/note.txt ')
	assert run(command) == ''
