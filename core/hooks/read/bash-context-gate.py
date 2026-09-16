#!/usr/bin/env python3
# PreToolUse: Bash — close the cat/head/grep bypass: extract workspace file paths from the
# command string and apply the same CONTEXT.md chain gate as context-gate.py.
# Known residual hole: dynamically constructed paths escape. See code/ROADMAP-verify.md W1.
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from chain import context_chain, paths_in
from hook_input import capability, is_subagent, load_seen, parse_stdin

HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def _strip_heredocs(command: str) -> str:
	"""Drop heredoc BODIES — the gate reads the command, never the text the command carries.

	`git commit -F - <<'EOF'` puts the commit message inside the command string, so a message
	that merely NAMES a path was read as a command touching that subtree and the gate demanded
	its CONTEXT.md before letting the commit through. Reported by Lucas (INBOX 2026-08-17) and
	hit twice more while writing this. A commit message is prose about work already done; the
	files it describes are staged, not read.

	The redirection target stays: in `cat > notes.md <<EOF`, `notes.md` is named OUTSIDE the
	body and is still extracted, so the cat/grep bypass this gate exists for is untouched.
	"""
	out, pos = [], 0
	for match in HEREDOC.finditer(command):
		marker = match.group(2)
		out.append(command[pos:match.end()])
		rest = command[match.end():]
		end = re.search(rf'^[ \t]*{re.escape(marker)}[ \t]*$', rest, re.M)
		pos = match.end() + (end.end() if end else len(rest))
	out.append(command[pos:])
	return ''.join(out)


def main() -> int:
	# The other half of context-chain; see the note in context-gate.py.
	if not feature_law.is_enabled('context-chain'):
		return 0
	raw, tool, tool_input, session_id, cwd = parse_stdin()
	# By capability, never by name: a harness may expose a second shell (PowerShell on Windows),
	# and this gate is the workspace's premise. See hook_input.capability.
	if capability(tool, tool_input) != 'shell':
		return 0
	if is_subagent(raw):
		return 0
	command = str(tool_input.get('command', ''))
	if not command:
		return 0
	seen = load_seen(session_id)
	unseen: list[str] = []
	for path in paths_in(_strip_heredocs(command), cwd, files_only=True):
		for ctx in context_chain(path):
			if str(ctx) not in seen and str(ctx) not in unseen:
				unseen.append(str(ctx))
	if not unseen:
		return 0
	print('CONTEXT GATE (Bash) - command touches files in a subtree whose context', file=sys.stderr)
	print('is not loaded. Read these CONTEXT.md files with the Read tool, then retry:', file=sys.stderr)
	for ctx in sorted(unseen):
		print(f'   {ctx}', file=sys.stderr)
	return 2


sys.exit(main())
