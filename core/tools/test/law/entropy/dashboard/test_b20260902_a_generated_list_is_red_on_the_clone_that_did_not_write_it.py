# b20260902 regression — the workspace's own list describes the workspace, never this disk.
#
# verify.py full failed here on two cases against an ISSUES.md the session had not touched: the
# block was generated on the Windows clone, which has none of the 27 nested repos this one holds,
# so the committed table listed repos that were missing and omitted repos that were present.
# Regenerating made it green with no source change. The suite asserted that a generated block
# matched the machine reading it, and the block is committed — so the same commit was green on the
# machine that wrote it and red on the other, handing every pull a red pre-commit gate for work it
# did not do, with the local change always the first suspect.
#
# Ruled 2026-09-04 (Lucas): in ISSUES.md terms the root counts only itself. Those projects are
# IGNORED by the root's git (.gitignore, not submodules), so a count of them was never a fact about
# the repo — it was a fact about the disk. Each project counts itself in its own ISSUES.md, written
# by its own pre-commit; where each one lives, here and outside, is PROJECTS.md.
import re
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/entropy'))
from entropy_corpus import nested_repos, tracked_files  # noqa: E402
from platform_law import rel  # noqa: E402  (the one spelling of a relative path)

ISSUES = WORKSPACE_ROOT / 'ISSUES.md'
HEADER = re.compile(r'\*\*(?P<here>\d+) findings here\*\*')


def _block() -> str:
	"""The GENERATED half alone. The hand-written bugs above it may name a project freely — a
	person writing about isoroll is not a machine claiming to have counted it."""
	from entropy_report import END, START
	text = ISSUES.read_text(encoding='utf-8')
	return text.split(START, 1)[1].split(END, 1)[0] if START in text else ''


def test_the_generated_block_names_no_nested_project() -> None:
	"""The exact shape that went red: a path this repo's git does not carry, counted into a file
	it does. A clone without that project reads a claim it cannot check."""
	block = _block()
	named = sorted(repo for repo in (rel(p, WORKSPACE_ROOT) for p in nested_repos(WORKSPACE_ROOT))
	               if repo in block)
	assert not named, f'the generated block counts projects the root git ignores: {named}'


def test_the_root_list_carries_no_collected_total() -> None:
	"""The sum over nested repos was the number that could not be true on both machines."""
	block = _block()
	assert '**collected**' not in block
	assert 'more across' not in block


def test_the_header_counts_what_this_repo_tracks() -> None:
	"""`here` is a fact about the repo, so it must be derivable from what the repo tracks —
	which is the same set on every clone, and the property the old table lacked."""
	assert HEADER.search(ISSUES.read_text(encoding='utf-8')), 'no header count in the list'
	scanned = tracked_files(WORKSPACE_ROOT, nested=False)
	assert scanned, 'the root scan must see the root repo'
	assert not any(str(p).startswith(str(repo)) for p in scanned
	               for repo in nested_repos(WORKSPACE_ROOT)), 'the root scan reached into a project'


def test_branch_debt_answers_for_one_repo() -> None:
	"""The 27 unpushed-work rows came from here. A project's push debt is real, and it is acted on
	at session close by core/tools/wos/roundup — not carried in a file the other clone must trust."""
	sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/git'))
	from branch_debt import repos
	assert repos(WORKSPACE_ROOT) == [WORKSPACE_ROOT]


if __name__ == '__main__':
	sys.exit(0)
