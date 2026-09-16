#!/usr/bin/env python3
# Notification, PreCompact — tell Lucas out of band when the session stopped needing a keyboard
# and started needing him.
#
# WHY THIS HOOK EXISTS (/ROADMAP.md § Cost). Five times the agent needed something only Lucas can
# do and said so where only an agent looks. Three of the five are MOMENTS rather than sentences —
# the session parked on a permission prompt, the session parked on a question, the harness
# compacting itself and saying so at the end — and a moment cannot be fixed by writing better.
# It needs a hook, which is this file, and a channel, which is core/tools/notify/telegram.
#
# WHY NOT A Stop HOOK FOR THE CLOSE OFFER. Stop fires at the end of EVERY response, so a channel
# hung there would say something after each turn and be muted inside a day. The close offer already
# has a moment that fires once per threshold — context-meter.py — so it rings from there instead.
# The cheapest registration is the one that already exists.
#
# ZERO MODEL TOKENS. This writes to stderr-free exit 0 and never to stdout: anything a hook prints
# on these moments would be injected into the very context the meter beside it is trying to spend
# less of. The whole point is a channel that costs the session nothing.
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import feature_law  # noqa: E402
from file_law import load_limits  # noqa: E402
from hook_input import parse_stdin  # noqa: E402
from platform_law import WORKSPACE_ROOT, session_state  # noqa: E402

RUN = ['sh', str(WORKSPACE_ROOT / 'core' / 'run')]
# Lucas is not at the keyboard — that is the premise. Nothing here is worth making him wait for,
# and a channel that hangs the session it was meant to rescue is worse than one that stays quiet.
TIMEOUT = 10


def last_sent(session_id: str) -> float:
	try:
		return float(session_state(f'notify_{session_id}.txt').read_text(encoding='utf-8').strip())
	except (OSError, ValueError):
		return 0.0


def mark(session_id: str) -> None:
	try:
		session_state(f'notify_{session_id}.txt').write_text(str(time.time()), encoding='utf-8', newline='\n')
	except OSError:
		pass


def muted(session_id: str, cooldown: int) -> bool:
	"""One message per cooldown per session.

	A parked session is re-notified by the harness while it stays parked, so without this the
	channel repeats itself at whatever interval the harness picked. A repeat carries no
	information Lucas does not already have, and a channel that repeats is a channel he mutes.
	"""
	return time.time() - last_sent(session_id) < cooldown


def line(raw: dict, cwd: str) -> str:
	"""One line, naming the workspace so a second session is not mistaken for this one.

	IN PORTUGUESE, unlike every other string in this tree (Lucas, 2026-09-15). The rest of the
	workspace is written for an agent and `lang` answers `en`; this is the one surface whose
	whole audience is Lucas, and a channel he reads at a glance should not ask him to translate.
	The harness's own `message` is relayed as it came — quoting it wrong is worse than quoting
	it in English.
	"""
	where = Path(cwd).name or 'workspace'
	if raw.get('hook_event_name') == 'PreCompact':
		return (f'{where}: a sessão se compactou. O que ela carregava virou resumo — peça pra ela '
		        f'se reancorar antes de confiar em resposta anterior a isto.')
	said = (raw.get('message') or '').strip()
	return f'{where}: parada, esperando você — {said}' if said else f'{where}: parada, esperando você.'


def tell(text: str) -> None:
	"""Say one line to Lucas, or nothing at all. The one entry point — context-meter.py calls it
	too, for the close offer, whose moment is a threshold crossing rather than a lifecycle event."""
	if not feature_law.is_enabled('notify'):
		return  # switched off: the moments pass and only the session knows they happened
	try:
		subprocess.run([*RUN, 'tools/notify/telegram', text], cwd=WORKSPACE_ROOT,
		               stdin=subprocess.DEVNULL, capture_output=True, text=True,
		               encoding='utf-8', errors='replace', timeout=TIMEOUT)
	except (OSError, subprocess.SubprocessError):
		pass  # an unreachable channel is a missed message, never a failed turn


def main() -> None:
	if not feature_law.is_enabled('notify'):
		return  # switched off: the moments pass and only the session knows they happened
	raw, _tool, _tool_input, session_id, cwd = parse_stdin()
	cooldown = load_limits().get('NOTIFY_COOLDOWN', 0)
	if muted(session_id, cooldown):
		return
	mark(session_id)
	tell(line(raw, cwd))


if __name__ == '__main__':
	try:
		main()
	except Exception:
		pass  # a channel must never cost the session it was built to rescue
	sys.exit(0)
