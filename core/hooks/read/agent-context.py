#!/usr/bin/env python3
# PreToolUse: Agent (collect) + SubagentStart (inject) — hand a worker the context for the paths it
# was pointed at, so the orchestrator does not have to remember to.
#
# Subagents are exempt from the context gate (core/hooks/SPECS.md, ruled 2026-08-15): a worker told
# to edit one function does not need the routing chain for everywhere it could have gone. That
# ruling moves the duty to the orchestrator, and this hook is what stops the duty being a discipline
# nobody keeps. It INDUCES, never blocks: a thin prompt yields a thin injection.
#
# Why two events. Measured, not assumed:
#   PreToolUse:Agent  sees `tool_input.prompt` but has NO agent_id, and its additionalContext goes
#                     back to the PARENT — useless for briefing the worker.
#   SubagentStart     has agent_id and CAN inject into the worker, but never sees the prompt.
# They share `prompt_id`, identical across both in one turn, so that is the join key. The blob is
# per-turn and expires with it.
#
# Known and accepted: several workers spawned in ONE turn share one blob, so each is briefed on the
# union of paths named across all of them. That is over-broad, never wrong; keying per worker is
# impossible because the only id arrives after the prompt is gone.
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from chain import context_chain, paths_in, summary_of
from platform_law import WORKSPACE_ROOT, rel, session_state  # noqa: E402

MAX_LINES = 12  # a briefing, not a corpus


def blob_file(prompt_id: str) -> Path:
	return session_state(f'claude_agent_ctx_{prompt_id or "none"}.txt')


def collect(data: dict) -> int:
	"""PreToolUse:Agent — resolve the chains for whatever the prompt names, and park them."""
	tool_input = data.get('tool_input') or {}
	text = f"{tool_input.get('prompt', '')}\n{tool_input.get('description', '')}"
	lines: list[str] = []
	for path in sorted(paths_in(text, str(data.get('cwd') or WORKSPACE_ROOT))):
		for ctx in context_chain(path):
			summary = summary_of(ctx)
			# The briefing is TEXT a worker reads, so the path is spelled by the boundary rather than
			# stripped by hand: a str().replace() of one machine's prefix left the whole absolute
			# path in place on every other clone, and this line is the one the worker actually sees.
			shown = rel(ctx)
			entry = f'- {shown} — {summary}' if summary else f'- {shown}'
			if entry not in lines:
				lines.append(entry)
	if not lines:
		return 0
	target = blob_file(str(data.get('prompt_id') or ''))
	existing = target.read_text(encoding='utf-8').splitlines() if target.exists() else []
	fresh = [line for line in lines if line not in existing]
	if fresh:
		# NAMED, NEVER INHERITED (core/tools/test/workspace/test_encoding_ratchet.py). The briefing carries an em dash, and a
		# bare open() encodes with the machine's codepage: written cp1252, read back as utf-8,
		# byte 0x97 raised and the WHOLE hook died -- so a worker got no briefing and the
		# orchestrator was never told. The read side below already named utf-8; only one half did.
		with target.open('a', encoding='utf-8', newline='\n') as handle:
			handle.write('\n'.join(fresh) + '\n')
	return 0


def inject(data: dict) -> int:
	"""SubagentStart — brief the worker with what its turn's prompts pointed at."""
	target = blob_file(str(data.get('prompt_id') or ''))
	if not target.exists():
		return 0
	lines = [line for line in target.read_text(encoding='utf-8').splitlines() if line.strip()][:MAX_LINES]
	if not lines:
		return 0
	body = ('Context for the paths your task names — the subtrees you are working in, one line '
	        'each. You are not required to read their CONTEXT.md files.\n' + '\n'.join(lines))
	print(json.dumps({'hookSpecificOutput': {
		'hookEventName': 'SubagentStart', 'additionalContext': body}}))
	return 0


def main() -> int:
	if not feature_law.is_enabled('agent-context-brief'):
		return 0  # switched off: briefing a worker goes back to being the orchestrator's discipline
	try:
		data = json.load(sys.stdin)
	except Exception:
		return 0
	if not isinstance(data, dict):
		return 0
	event = data.get('hook_event_name')
	if event == 'SubagentStart':
		return inject(data)
	if data.get('tool_name') == 'Agent':
		return collect(data)
	return 0


sys.exit(main())
