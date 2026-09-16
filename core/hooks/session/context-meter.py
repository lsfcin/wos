#!/usr/bin/env python3
# UserPromptSubmit — say what the next turn costs, once per threshold crossed.
#
# The session cannot see its own size, so the decision to hand off is made blind and
# usually made late. This reads the size the API already reported on the last assistant
# turn (input + cache read + cache write) and announces the two thresholds in limits.env.
# Zero model tokens until a threshold is crossed, and it never blocks a prompt.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # notify.py and transcript.py, beside this

import feature_law  # noqa: E402
import notify  # noqa: E402
import transcript  # noqa: E402
from file_law import load_limits  # noqa: E402
from hook_input import parse_stdin  # noqa: E402
from platform_law import session_state  # noqa: E402

# The meter names /roundup and nothing else. Where the resume prompt lands is the skill's
# business (core/skills/handoff.md → outputs/handoff.md); repeating the path here would put
# the same fact in two files and hand the agent a second thing to decide about.


def state_file(session_id: str) -> str:
	return str(session_state(f'claude_ctx_meter_{session_id}.txt'))


def announced(session_id: str) -> int:
	try:
		with open(state_file(session_id), encoding='utf-8') as f:
			return int(f.read().strip() or 0)
	except (OSError, ValueError):
		return 0


def mark(session_id: str, threshold: int) -> None:
	try:
		with open(state_file(session_id), 'w', encoding='utf-8', newline='\n') as f:
			f.write(str(threshold))
	except OSError:
		pass


def message(ctx: int, crossed: int, loud: int) -> str:
	size = f'{ctx // 1000}k'
	if crossed >= loud:
		return (f'CONTEXT WINDOW: {size} used — turns now cost ~2x a fresh session and stay '
		        f'there. Run /roundup to close this session once the current thread is done.')
	return (f'CONTEXT WINDOW: {size} used — turn cost climbs ~45% from here and never drops '
	        f'back. At a good stopping point, run /roundup to close this session; if this '
	        f'thread is nearly done, ignore this and finish.')


def main() -> None:
	if not feature_law.is_enabled('context-meter'):
		return  # switched off: the session crosses its bands without being told
	raw, _tool, _tool_input, session_id, cwd = parse_stdin()
	path = transcript.find(raw, session_id, cwd)
	if not path:
		return
	ctx = transcript.last_context(path)
	limits = load_limits()
	warn, loud = limits.get('CTX_WARN', 0), limits.get('CTX_LOUD', 0)
	crossed = max((t for t in (warn, loud) if t and ctx >= t), default=0)
	if not crossed or crossed <= announced(session_id):
		return
	mark(session_id, crossed)
	print(message(ctx, crossed, loud))
	# The close offer is one of the five things that only ever reached agent-facing writing
	# (/ROADMAP.md § Cost). It is already once-per-threshold here, so it needs no moment of its
	# own — and a hook at the end of every response would have to invent a reason to stay quiet.
	# The two wordings differ because the two readers do: the line above is an instruction to an
	# agent mid-thread, this one is a fact for Lucas wherever he is.
	notify.tell(f'{Path(cwd).name or "workspace"}: contexto em {ctx // 1000}k — daqui pra frente '
	            f'cada turno custa mais e não volta a baratear. Hora de fechar com /roundup.')


if __name__ == '__main__':
	try:
		main()
	except Exception:
		pass  # a meter must never cost a prompt
	sys.exit(0)
