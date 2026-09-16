#!/usr/bin/env python3
# statusLine — the context window as a line that is always on screen, and the trend across it.
#
# WHY THIS EXISTS (/ROADMAP.md § Cost). context-meter.py beside it speaks ONCE per threshold, so
# between 100k and 200k Lucas learns nothing, and the first thing he hears about a session getting
# expensive is that it already is. He asked for the trend between the two numbers, not a third
# announcement: a meter he can glance at rather than one that interrupts.
#
# WHY A STATUSLINE AND NOT ANOTHER HOOK. The harness renders this outside the conversation, so it
# reaches Lucas's eyes without reaching the model's context — the one place in this workspace where
# telling him something costs literally zero tokens. Any hook that printed the same line every turn
# would be paying for the report out of the very budget the report is about.
#
# WHAT IT DRAWS: the bar spans 0 to CTX_LOUD, `!` marks CTX_WARN, and the delta is per TURN rather
# than per render — the number moves when the session moves, not when the terminal repaints.
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import feature_law  # noqa: E402
import transcript  # noqa: E402
from file_law import load_limits  # noqa: E402
from platform_law import session_state  # noqa: E402

CELLS = 12


def remembered(session_id: str) -> tuple[int, int]:
	"""The last context this session drew, and the step that got it there."""
	try:
		was, step = session_state(f'statusline_{session_id}.txt').read_text(encoding='utf-8').split()
		return int(was), int(step)
	except (OSError, ValueError):
		return 0, 0


def remember(session_id: str, ctx: int, step: int) -> None:
	try:
		session_state(f'statusline_{session_id}.txt').write_text(
			f'{ctx} {step}', encoding='utf-8', newline='\n')
	except OSError:
		pass


def bar(ctx: int, warn: int, loud: int) -> str:
	"""0 to LOUD in CELLS cells, with WARN marked where it falls. Past LOUD the bar is full and
	the number beside it is what carries the news — a bar that keeps growing off the end says
	less than one that is visibly maxed.

	WARN IS A DIVIDER BETWEEN CELLS, NOT A CELL. Marking the warn cell overwrote whatever that
	cell was saying, so the bar spent its own resolution on the annotation. A divider adds a
	character instead of consuming one.

	The bar resolves LOUD/CELLS and no finer, so two readings a few thousand tokens apart draw
	the same — which is true rather than a defect: a few thousand tokens IS the same place. The
	number beside it is the precise half, and the crossing itself is context-meter.py's to say."""
	if not loud:
		return '.' * CELLS
	filled = min(CELLS, round(CELLS * ctx / loud))
	mark = min(CELLS, int(CELLS * warn / loud))
	cells = ['#' if i < filled else '.' for i in range(CELLS)]
	return ''.join(cells[:mark]) + '!' + ''.join(cells[mark:])


def line(ctx: int, step: int, warn: int, loud: int) -> str:
	trend = 'flat' if abs(step) < 1000 else f'{step // 1000:+d}k/turn'
	where = ' /roundup' if ctx >= loud else ''
	return f'ctx {ctx // 1000}k [{bar(ctx, warn, loud)}] {trend}{where}'


def main() -> None:
	if not feature_law.is_enabled('statusline'):
		return  # switched off: the line is blank and the meter's two crossings are all he gets
	raw = json.loads(sys.stdin.read() or '{}')
	session_id = raw.get('session_id', '')
	path = transcript.find(raw, session_id, raw.get('cwd', ''))
	if not path:
		return
	ctx = transcript.last_context(path)
	if not ctx:
		return
	was, step = remembered(session_id)
	if ctx != was:
		step = ctx - was if was else 0
		remember(session_id, ctx, step)
	limits = load_limits()
	print(line(ctx, step, limits.get('CTX_WARN', 0), limits.get('CTX_LOUD', 0)))


if __name__ == '__main__':
	try:
		main()
	except Exception:
		pass  # a blank statusline is a missing report; a crashing one is a broken terminal
	sys.exit(0)
