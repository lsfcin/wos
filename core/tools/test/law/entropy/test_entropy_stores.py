# T0 the two doubt stores (core/SPECS.md § AD-16 band 1): an experiment states its own format, and
# a judged reference carries a source level. Zero-token, runs in verify-fast.
#
# These are the rules this workspace cites as proof it knows how to doubt, and until 2026-08-18
# nothing verified either — INDUCED wearing ENFORCED's costume, which is the defect that front
# exists to catch. Both stores are small and closed, so the check is total and the real corpus is
# asserted clean below rather than ridden on a ceiling.
from pathlib import Path

import entropy_stores as stores
from conftest import WORKSPACE_ROOT

COMPLETE = """# t
> Does the thing cost what we think it costs?

## Method
`core/tools/wos/session/usage --days 7`

## Results
| date | n |
|---|---|
| 2026-08-18 | 3 |

## What changed
nothing yet

## Limitations
One machine, one week.
"""


def _experiment(tmp_path: Path, body: str, name: str = 'thing.md') -> list:
    target = tmp_path / 'core' / 'experiments'
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    path.write_text(body, encoding='utf-8', newline='\n')
    return stores.experiment_hits([path])


def test_a_complete_experiment_passes(tmp_path):
    assert _experiment(tmp_path, COMPLETE) == []


def test_a_missing_limitations_section_is_a_finding(tmp_path):
    """The section that earned the check. The output-cost number was wrong by 2x for three weeks,
    and what would have caught it is the line saying what the instrument cannot tell you."""
    hits = _experiment(tmp_path, COMPLETE.replace('## Limitations\nOne machine, one week.\n', ''))
    assert len(hits) == 1 and '## Limitations' in hits[0]


def test_what_changed_is_required_even_when_the_answer_is_nothing(tmp_path):
    """`nothing yet` is an answer; an absent section hides a measurement nobody acted on."""
    hits = _experiment(tmp_path, COMPLETE.replace('## What changed\nnothing yet\n', ''))
    assert len(hits) == 1 and '## What changed' in hits[0]


def test_the_question_line_must_be_line_two(tmp_path):
    hits = _experiment(tmp_path, COMPLETE.replace('> Does the thing cost what we think it costs?',
                                                  'Does it cost what we think?'))
    assert len(hits) == 1 and 'question' in hits[0]


def test_the_directorys_own_two_documents_are_not_experiments(tmp_path):
    """CONTEXT.md and SPECS.md describe the format; judging them by it makes the format its own
    first violation."""
    for name in ('CONTEXT.md', 'SPECS.md'):
        assert _experiment(tmp_path, '# x\n> y\n', name) == []


def _refs(tmp_path: Path, body: str) -> list:
    target = tmp_path / 'core' / 'refs'
    target.mkdir(parents=True, exist_ok=True)
    path = target / 'REFS.md'
    path.write_text(body, encoding='utf-8', newline='\n')
    return stores.ref_level_hits([path])


def test_a_judged_reference_needs_a_level(tmp_path):
    hits = _refs(tmp_path, '## Judged\n\n- [A paper](https://example.org/x) — a finding.\n')
    assert len(hits) == 1 and 'no source level' in hits[0]


def test_a_tiered_reference_passes(tmp_path):
    assert _refs(tmp_path, '## Judged\n\n- `[P]` [A paper](https://example.org/x) — a finding.\n') == []


def test_the_unjudged_queue_is_exempt(tmp_path):
    """Capture stays free. A link earns its level when it is promoted, and demanding one at capture
    time is what turns an intake queue into a chore."""
    assert _refs(tmp_path, '## Unjudged\n\n- [A paper](https://example.org/x) — maybe.\n') == []


def test_a_prose_line_holding_a_link_is_not_a_reference(tmp_path):
    """Only a bullet is a ref line. A sentence in the file's head mentioning a URL is prose, and a
    check that read it would make the file's own explanation of itself a violation."""
    assert _refs(tmp_path, 'See https://example.org/x for context.\n\n## Judged\n') == []


def test_the_real_stores_are_clean():
    """The rule is in force over the live corpus, which is what makes the check a fact about this
    workspace rather than a capability sitting beside it."""
    files = (sorted((WORKSPACE_ROOT / 'core/experiments').glob('*.md'))
             + [WORKSPACE_ROOT / 'core/refs/REFS.md'])
    hits = stores.experiment_hits(files) + stores.ref_level_hits(files)
    assert hits == [], '\n'.join(hits)
