# b20260901 regression — this machine's answers override the shared ones and never travel.
#
# core/profile.txt is versioned and its head claimed to hold the answers "for THIS machine". Two
# clones pull it, on two operating systems with genuinely different feature sets — `latex`,
# `telegram-capture` and the apt-only deps are not the same question here as there — so
# `features --on/--off` on one landed on the other, and the permission level is one line in the
# same file. Every other per-machine artifact here is generated and gitignored.
#
# Ruled 2026-09-04 (Lucas): a gitignored core/profile.local.txt overrides the base row by row,
# the shape .claude/settings.local.json already uses. The base stays versioned because a gitignored
# answers file has no diff to review, and that diff is what the base exists for.
import importlib.util
import subprocess
import sys
from pathlib import Path

import feature_law as law

ROOT = Path(__file__).resolve().parents[5]


def _features_tool():
	"""The CLI loaded as a module — it is extensionless, so import needs the path spelled out."""
	spec = importlib.util.spec_from_loader(
		'features_cli', importlib.machinery.SourceFileLoader(
			'features_cli', str(ROOT / 'core/tools/wos/features')))
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def test_the_local_file_is_read_on_top_of_the_shared_one(monkeypatch, tmp_path) -> None:
	base, local = tmp_path / 'profile.txt', tmp_path / 'profile.local.txt'
	base.write_text('kind\tkey\tvalue\ntoggle\tlatex\ton\ntoggle\tcaveman\ton\n',
	                encoding='utf-8', newline='\n')
	local.write_text('kind\tkey\tvalue\ntoggle\tlatex\toff\n', encoding='utf-8', newline='\n')
	monkeypatch.setattr(law, 'PROFILE_FILE', base)
	monkeypatch.setattr(law, 'LOCAL_PROFILE_FILE', local)

	answers = law.load_profile()['toggle']
	assert answers['latex'] == 'off', 'this machine answered, and its answer must win'
	assert answers['caveman'] == 'on', 'a question this machine never answered stays inherited'
	assert law.is_enabled('latex') is False


def test_a_clone_with_no_local_file_still_gets_every_answer(monkeypatch, tmp_path) -> None:
	"""The file is optional by construction: a fresh clone has only the base and must run."""
	base = tmp_path / 'profile.txt'
	base.write_text('kind\tkey\tvalue\ntoggle\tlatex\ton\n', encoding='utf-8', newline='\n')
	monkeypatch.setattr(law, 'PROFILE_FILE', base)
	monkeypatch.setattr(law, 'LOCAL_PROFILE_FILE', tmp_path / 'absent.txt')
	assert law.load_profile()['toggle'] == {'latex': 'on'}


def test_the_local_file_is_not_versioned() -> None:
	"""The whole point: an answer typed on one clone must not reach the other through git."""
	done = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', 'core/profile.local.txt'],
	                      capture_output=True, text=True, encoding='utf-8')
	assert done.returncode == 0, 'core/profile.local.txt must be ignored, or the split is undone'


def test_a_switch_is_written_where_this_machine_is_asked(tmp_path) -> None:
	"""`features --off` writes the override and leaves the shared base byte-identical.

	The base is the file a pull carries. A flip that edited it is the bug itself, so this asserts
	on the bytes rather than on the answer the merge reports afterwards.
	"""
	tool = _features_tool()
	base_before = (ROOT / 'core/profile.txt').read_bytes()
	tool.LOCAL = tmp_path / 'profile.local.txt'
	assert tool._write_toggle('latex', 'off') == 0

	assert 'toggle\tlatex\toff' in tool.LOCAL.read_text(encoding='utf-8')
	assert (ROOT / 'core/profile.txt').read_bytes() == base_before


if __name__ == '__main__':
	sys.exit(0)
