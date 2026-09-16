# T0 the project map (core/SCHEMA.md § The .md type system): every internal project is declared,
# and the declaration cannot drift from the one place git already names them.
#
# The projects are separate repos IGNORED by the workspace's git, not submodules — so nothing the
# root repo carries knows their remotes, and PROJECTS.md is written by hand. What keeps a
# hand-written table honest is that its key column has an independent source: the project block in
# .gitignore, which is tracked, and therefore the same on every clone whether or not a given
# project is checked out there. Reading the DISK instead would rebuild the machine-dependence that
# b20260902 was about.
import re
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT, needs

PROJECTS = WORKSPACE_ROOT / 'PROJECTS.md'
ROW = re.compile(r'^\|\s*`([^`]+)`\s*\|', re.MULTILINE)


def declared_in_gitignore() -> set:
	"""Project paths as .gitignore declares them — asked of the module that owns the rule.

	Restating the parse here is what this file is built to catch one level up: a second copy of a
	rule is where two readers start disagreeing. entropy_corpus.declared_projects is the one copy,
	and the pre-commit's list stage asks it the same question.
	"""
	from entropy_corpus import declared_projects
	return declared_projects(WORKSPACE_ROOT)


def listed_in_projects() -> set:
	return set(ROW.findall(PROJECTS.read_text(encoding='utf-8')))


def test_every_declared_project_has_a_row() -> None:
	needs('PROJECTS.md')
	missing = sorted(declared_in_gitignore() - listed_in_projects())
	assert not missing, (
		f'{missing} are declared in .gitignore and absent from PROJECTS.md — a project nobody can '
		f'find is the state this file exists to end')


def test_every_row_names_a_declared_project() -> None:
	needs('PROJECTS.md')
	"""The other direction, and the one a rename breaks: a row whose path git never ignores is
	pointing at a directory that either moved or was never a project."""
	stale = sorted(listed_in_projects() - declared_in_gitignore())
	assert not stale, f'{stale} have a row in PROJECTS.md and no line in .gitignore'


def test_the_table_reads_the_same_on_every_clone() -> None:
	needs('PROJECTS.md')
	"""Nothing here may depend on what is checked out. The trap this file was written to avoid is
	the one b20260902 sprang: a tracked table that describes one machine's disk."""
	assert declared_in_gitignore(), 'no projects declared — the parse rule has drifted'
	assert listed_in_projects() == declared_in_gitignore()


if __name__ == '__main__':
	sys.exit(0)
