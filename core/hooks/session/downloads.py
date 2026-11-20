#!/usr/bin/env python3
# UserPromptSubmit — when the prompt says "baixei", name the files that just landed.
#
# Lucas says he downloaded something and the session then hunts three folders for it, by hand,
# every time. This answers before the hunt starts. Every other prompt pays nothing: the regex is
# the whole cost, and the folders are only listed after it matched (ROADMAP.md, [downloads-hook]).
# The folders are spelled from the workspace root and $HOME at runtime, never as a machine path.
import os
import re
import sys
import time
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))

import feature_law  # noqa: E402
from file_law import load_limits  # noqa: E402
from hook_input import parse_stdin  # noqa: E402

ROOT = HOOKS.parents[1]
SAID = re.compile(r'\b(baix(?:ei|ar|ou|ando|ad[oa]s?)|downloads?)\b', re.IGNORECASE)


def folders(root: Path, home: Path) -> list[Path]:
	"""Where a download lands: the workspace's own folder first, its Drive sync, then the system one."""
	return [root / 'Downloads', root / 'Downloads' / 'workspace-drive', home / 'Downloads']


def recent(dirs: list[Path], now: float, window: int) -> list[tuple[float, int, Path]]:
	"""(age, size, path) of every visible file younger than the window, newest first.

	Age is mtime, which a browser stamps when the download finishes. ctime would also catch a file
	MOVED in with an old mtime, but nothing can backdate it, so no test could tell old from new."""
	seen: set[Path] = set()
	found = []
	for folder in dirs:
		try:
			real = folder.resolve()
			if real in seen:
				continue
			seen.add(real)
			entries = list(os.scandir(folder))
		except OSError:
			continue
		for entry in entries:
			if entry.name.startswith('.'):
				continue
			try:
				if not entry.is_file():
					continue
				stat = entry.stat()
			except OSError:
				continue
			age = max(0.0, now - stat.st_mtime)
			if age <= window:
				found.append((age, stat.st_size, Path(entry.path)))
	return sorted(found)


def _size(n: int) -> str:
	for unit in ('B', 'KB', 'MB', 'GB'):
		if n < 1024 or unit == 'GB':
			return f'{n:.0f} {unit}' if unit == 'B' else f'{n:.1f} {unit}'
		n /= 1024
	return ''


def report(rows: list[tuple[float, int, Path]], cap: int, window: int, searched: list[Path]) -> str:
	minutes = window // 60
	if not rows:
		return (f'DOWNLOADS: nothing in the last {minutes} min in '
		        + ', '.join(str(p) for p in searched) + '.')
	lines = [f'DOWNLOADS — last {minutes} min, newest first:']
	lines += [f'  {age / 60:4.0f} min  {_size(size):>9}  {path}' for age, size, path in rows[:cap]]
	if len(rows) > cap:
		lines.append(f'  … {len(rows) - cap} more')
	return '\n'.join(lines)


def main() -> int:
	if not feature_law.is_enabled('downloads'):
		return 0
	raw = parse_stdin()[0]
	if not SAID.search(str(raw.get('prompt') or '')):
		return 0
	limits = load_limits()
	window = limits['DOWNLOADS_WINDOW']
	dirs = folders(ROOT, Path.home())
	print(report(recent(dirs, time.time(), window), limits['DOWNLOADS_MAX'], window, dirs))
	return 0


if __name__ == '__main__':
	sys.exit(main())
