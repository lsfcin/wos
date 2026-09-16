# b20260901 regression — a tracked file with no comment syntax still earns its routing row.
#
# `.agents/hooks.json` was tracked, described, and had a row — and the first sync of `.agents/` in
# months deleted it. workspace_scanner.is_scanned admits a file only when its suffix is in
# workspace_meta.ALL_EXTS, which had no `.json`, so the row could not be rebuilt: the directory
# ended up describing itself with its load-bearing file missing. Every config a harness dictates is
# a `.json` (`.agents/hooks.json`, `.zcode/config.json`), which is exactly the class the routing
# table exists to name.
#
# Ruled 2026-09-04 (Lucas): descriptions for such a file live in core/hooks/described.txt, the same
# shape as extensionless.txt, vendored.txt and generated.txt beside it — the law is the data file,
# never the checker. The list is narrow on purpose: a format that CAN carry a comment describes
# itself at the source, and these cases hold that line.
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT, carries

from file_law import described  # noqa: E402
from workspace_meta import ALL_EXTS, file_description  # noqa: E402
from workspace_scanner import is_scanned  # noqa: E402


def test_a_tracked_json_is_scanned() -> None:
	"""The row could not be rebuilt because the file was invisible to the generator."""
	assert '.json' in ALL_EXTS
	assert is_scanned(WORKSPACE_ROOT / '.agents/hooks.json')


def test_the_file_that_lost_its_row_can_describe_itself_again() -> None:
	description = file_description(WORKSPACE_ROOT / '.agents/hooks.json')
	assert description and description.strip()


def test_every_declared_path_is_really_tracked() -> None:
	"""A description for a file git does not carry describes a tree no reader has.

	The same failure `workspace_scanner.carried` exists to stop one layer up, and the reason this
	list can stay narrow: a stale entry is a test failure rather than a row nobody notices.
	"""
	import subprocess
	done = subprocess.run(['git', '-C', str(WORKSPACE_ROOT), 'ls-files', '--', *described()],
	                      capture_output=True, text=True, encoding='utf-8')
	carried_paths = {line.strip() for line in done.stdout.splitlines() if line.strip()}
	# A row naming a tree this checkout does not carry is unanswerable, not stale: the list crosses
	# whole into the public repo, which has no academy/ or code/ to describe. Judged by the TREE,
	# so a row pointing at a file deleted from a tree that IS here still fails.
	here = {p for p in described() if carries(p)}
	assert here <= carried_paths, sorted(here - carried_paths)


def test_the_list_stays_narrow() -> None:
	"""Only a format with NO comment syntax belongs here. Anything else describes itself where it
	lives, beside what it describes — a data file that starts absorbing those is a net."""
	from workspace_meta import COMMENT_RE
	commentable = sorted(p for p in described() if Path(p).suffix in COMMENT_RE)
	assert not commentable, f'{commentable} can carry a first-line comment — describe them there'


if __name__ == '__main__':
	sys.exit(0)
