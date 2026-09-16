# The session's own transcript, read cheaply: where it is, and what the last turn carried.
#
# EXTRACTED FROM context-meter.py (2026-09-15), when the statusline became its second reader. The
# alternative was a second copy of the tail scan, which is the drift core/hooks/CONTEXT.md exists to
# catch — and the copy would have been the expensive kind, since both readers run on a hot path.
#
# WHY NOT core/tools/wos/session/session_log.py, which also replays transcripts: that module answers
# what a whole session COST, walking every record. These two callers need the last number only, and
# one of them redraws on every keystroke. Reading forward to answer a question about the end is the
# wrong shape however good the module is.
import json
import os
from pathlib import Path

# The tail alone. A long session's transcript runs to megabytes, and the answer is always in the
# final records — so the scan is bounded by what it may read, not by how long the session ran.
TAIL_BYTES = 512 * 1024


def find(raw: dict, session_id: str, cwd: str) -> str:
	"""The payload names it when it can; otherwise it is <cwd-name>/<session_id>.jsonl."""
	given = raw.get('transcript_path')
	if given and os.path.isfile(given):
		return given
	name = cwd.replace('/', '-')
	candidate = Path.home() / '.claude' / 'projects' / name / f'{session_id}.jsonl'
	return str(candidate) if candidate.is_file() else ''


def last_context(path: str) -> int:
	"""Context carried by the most recent main-chain assistant turn, in tokens."""
	try:
		with open(path, 'rb') as f:
			f.seek(0, os.SEEK_END)
			f.seek(max(0, f.tell() - TAIL_BYTES))
			chunk = f.read()
	except OSError:
		return 0
	for line in reversed(chunk.split(b'\n')):
		if b'"usage"' not in line:
			continue
		try:
			event = json.loads(line)
		except (json.JSONDecodeError, UnicodeDecodeError):
			continue
		if event.get('type') != 'assistant' or event.get('isSidechain'):
			continue
		usage = (event.get('message') or {}).get('usage') or {}
		if not usage:
			continue
		return (usage.get('input_tokens', 0)
		        + usage.get('cache_read_input_tokens', 0)
		        + usage.get('cache_creation_input_tokens', 0))
	return 0
