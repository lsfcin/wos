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
	"""The payload names it when it can; otherwise it is <cwd-name>/<session_id>.jsonl or AGY brain."""
	given = raw.get('transcript_path')
	if given and os.path.isfile(given):
		return given
	name = cwd.replace('/', '-')
	candidate = Path.home() / '.claude' / 'projects' / name / f'{session_id}.jsonl'
	if candidate.is_file():
		return str(candidate)
	agy_candidate = Path.home() / '.gemini' / 'antigravity' / 'brain' / session_id / '.system_generated' / 'logs' / 'transcript.jsonl'
	if agy_candidate.is_file():
		return str(agy_candidate)
	return ''


def _tail(path: str) -> bytes:
	try:
		with open(path, 'rb') as f:
			f.seek(0, os.SEEK_END)
			size = f.tell()
			f.seek(max(0, size - TAIL_BYTES))
			return f.read()
	except OSError:
		return b''


def last_context(path: str) -> int:
	"""Last recorded input, in tokens; native cached input is included already."""
	chunk = _tail(path)
	# 1. Claude Code schema: search backward for assistant turn usage
	for line in reversed(chunk.split(b'\n')):
		try:
			event = json.loads(line)
		except (json.JSONDecodeError, UnicodeDecodeError):
			continue
		if event.get('type') == 'compacted':
			return 0  # no current measurement after compaction until a response records one
		if event.get('type') == 'event_msg' and event.get('payload', {}).get('type') == 'token_count':
			usage = (event['payload'].get('info') or {}).get('last_token_usage') or {}
			if usage:
				return usage.get('input_tokens', 0)  # cached input is already included
		if event.get('type') == 'token_usage_record' and event.get('payload', {}).get('usage'):
			return event['payload']['usage'].get('input_tokens', 0)
		if event.get('type') != 'assistant' or event.get('isSidechain'):
			continue
		usage = (event.get('message') or {}).get('usage') or {}
		if not usage:
			continue
		return (usage.get('input_tokens', 0)
		        + usage.get('cache_read_input_tokens', 0)
		        + usage.get('cache_creation_input_tokens', 0))

	# 2. Antigravity schema: character-based estimate (chars / 3.6) since most recent CHECKPOINT
	if b'"step_index"' in chunk:
		last_cp = chunk.rfind(b'"CHECKPOINT"')
		if last_cp != -1:
			line_start = chunk.rfind(b'\n', 0, last_cp)
			active_bytes = chunk[line_start:] if line_start != -1 else chunk[last_cp:]
		else:
			active_bytes = chunk
		return int(len(active_bytes) / 3.6)

	return 0


def context_limit(path: str) -> int:
	"""The last runtime-reported window, never the model's documented maximum."""
	for line in reversed(_tail(path).splitlines()):
		try:
			event = json.loads(line)
		except (ValueError, UnicodeError):
			continue
		if event.get('type') == 'event_msg' and event.get('payload', {}).get('type') == 'token_count':
			return (event['payload'].get('info') or {}).get('model_context_window') or 0
	return 0


def is_compacted(path: str) -> bool:
	"""True if this session has undergone mid-session compaction (CHECKPOINT with step_index > 1)."""
	try:
		with open(path, 'rb') as f:
			data = f.read()
	except OSError:
		return False
	for line in data.splitlines():
		if b'"compacted"' not in line:
			continue
		try:
			if json.loads(line).get('type') == 'compacted':
				return True
		except (ValueError, UnicodeError):
			continue
	if b'"step_index"' not in data or b'"CHECKPOINT"' not in data:
		return False
	idx = 0
	while True:
		pos = data.find(b'"CHECKPOINT"', idx)
		if pos == -1:
			break
		line_start = data.rfind(b'\n', 0, pos)
		line_end = data.find(b'\n', pos)
		line = data[line_start + 1:line_end if line_end != -1 else None]
		try:
			event = json.loads(line)
			if event.get('type') == 'CHECKPOINT' and event.get('step_index', 0) > 1:
				return True
		except (json.JSONDecodeError, UnicodeDecodeError):
			pass
		idx = pos + 12
	return False
