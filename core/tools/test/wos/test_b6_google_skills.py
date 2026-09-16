# B6 regression — every Google-backed tool family has a skill wrapper.
#
# Half the families carried a core/skills/<name>.md and half did not, on no stated rule; the
# question re-litigated itself every time a family landed. Ruled 2026-08-31 (Lucas): add where
# missing, never half — the rule is a sentence in core/tools/SPECS.md § Adding a tool, and this
# spec is the sentence made checkable. Scope is the Google families the ruling names; a family
# outside the set is a SPECS change first, not a silent pass here.
#
# IT ASKS THE REGISTRY, NOT THE FILENAME. The wrapper's name used to be guessed here from the
# provider — `gmail.md` for mail/gmail — which made this file a second spelling of a convention it
# does not own, and the convention moved under it: Lucas ruled 2026-09-16 that a skill takes the
# FAMILY name and leaves the vendor on the leaf, per core/tools/CONTEXT.md. The `ships` column says
# which skill file belongs to which tool family outright, so reading it is the same law once.
from conftest import WORKSPACE_ROOT

FAMILIES = ('mail', 'calendar', 'files', 'slides', 'forms', 'docs')


def _wrappers() -> dict[str, str]:
    """Family -> the skill file some feature row ships alongside it."""
    rows = [ln.split('\t') for ln in
            (WORKSPACE_ROOT / 'core/features.txt').read_text(encoding='utf-8').split('\n')
            if ln and not ln.startswith('#') and '\t' in ln]
    header = rows[0]
    out = {}
    for row in rows[1:]:
        ships = dict(zip(header, row)).get('ships', '')
        skills = [p for p in ships.split(',') if p.startswith('core/skills/')]
        for path in ships.split(','):
            if path.startswith('core/tools/') and skills:
                out[path.split('/')[2]] = skills[0]
    return out


def test_every_google_family_has_a_skill():
    wrappers = _wrappers()
    missing = [family for family in FAMILIES if family not in wrappers]
    assert not missing, (
        f'Google-backed families with no skill wrapper declared: {missing}. Add the skill at '
        f'core/skills/<family>.md and name it in that feature row\'s `ships` column')


def test_a_declared_wrapper_is_really_there():
    absent = [f'{family} -> {path}' for family, path in _wrappers().items()
              if family in FAMILIES and not (WORKSPACE_ROOT / path).is_file()]
    assert not absent, f'a row ships a skill file that does not exist: {absent}'


def test_the_rule_is_stated_where_the_next_family_reads_it():
    specs = (WORKSPACE_ROOT / 'core/tools/SPECS.md').read_text(encoding='utf-8')
    assert 'Every Google-backed family gets a skill wrapper' in specs
