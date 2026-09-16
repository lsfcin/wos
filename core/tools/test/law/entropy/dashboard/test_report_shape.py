# T0 what the report shows, and what it stays quiet about: a clean check is a table row, never a
# section.
#
# Every check got a heading, a restated note and the word "Clean." until 2026-09-05, so 17 of 23
# sections said nothing in six lines each — ~102 of the workspace ISSUES.md's 323, all of it
# repeating a summary row that already read zero. The file read as a large list with five open
# bugs in it, and the question it provoked ("are we forgetting to delete?") had the wrong answer
# available: nothing was being forgotten, the generator was the bulk.
#
# core/hooks/SPECS.md states the rule one layer up — a gate whose biggest number is not a problem
# trains its reader to ignore it — and this spec is that rule pointed at the reporter itself.
import sys

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/entropy/dashboard'))
import entropy_report  # noqa: E402

KEYS = [key for key, _, _ in entropy_report.SECTIONS]


def report(**found) -> str:
	"""The rendered block, carrying findings only for the keys named."""
	findings = {key: list(found.get(key, [])) for key in KEYS}
	return entropy_report.render(findings, 10, WORKSPACE_ROOT)


def test_every_check_is_counted_even_when_it_is_clean():
	"""The table is the complete inventory, and dropping the sections may not shrink it."""
	page = report()
	for _key, title, _note in entropy_report.SECTIONS:
		assert f'| {title} | 0 |' in page, f'{title} left the summary table'


def test_a_clean_check_gets_no_section():
	page = report()
	assert '###' not in page, 'a check with nothing to say still wrote a heading'
	assert 'Clean.' not in page


def test_a_check_with_findings_gets_its_heading_its_note_and_its_items():
	key, title, note = entropy_report.SECTIONS[0]
	page = report(**{key: ['some/file.md:1 something drifted']})
	assert f'### {title}' in page and f'*{note}*' in page
	assert 'some/file.md:1 something drifted' in page
	assert f'| {title} | 1 |' in page


def test_the_headline_counts_what_has_no_section():
	"""The total is over findings, not over sections, or silencing a check would silence its count."""
	first, second = entropy_report.SECTIONS[0][0], entropy_report.SECTIONS[1][0]
	page = report(**{first: ['a:1 x'], second: ['b:2 y', 'c:3 z']})
	assert '**3 findings here**' in page
