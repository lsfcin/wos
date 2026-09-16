# T0 the norms layer (core/SCHEMA-layers.md § Layer: norm): the always-loaded rule block is generated,
# and generating it is what makes a rule switchable.
#
# WHY THIS IS ITS OWN FILE. test_features.py asks whether the registry's DATA is complete and
# test_features_wiring.py whether a row's switch RUNS. Neither can ask the question that matters
# here: does the file every session is forced to load still say what it said? AGENTS.md is the one
# artifact where a generator bug is paid by every session in the workspace before anyone notices,
# so the round-trip is asserted against the source of truth rather than trusted.
import os
import re
import subprocess
import sys

import feature_law as law
from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core' / 'hooks' / 'routing'))
import norms  # noqa: E402

AGENTS = WORKSPACE_ROOT / 'AGENTS.md'
NORMS_DIR = WORKSPACE_ROOT / 'core' / 'norms'
FRONTMATTER = re.compile(r'\A---\nname: ([a-z0-9-]+)\ndescription: (.+)\n---\n', re.M)


def _rows():
    return [r for r in law.load_registry() if 'norms' in law.groups(r)]


def test_every_norm_file_is_declared_and_every_declared_norm_exists():
    """The layer's join, both directions.

    A file nobody declared is never published and reads as a rule that is simply ignored; a row
    naming no file is a registry claiming to switch something that does not exist. Both are silent,
    which is why they are asserted rather than eyeballed.
    """
    declared = {r['name'] for r in _rows()}
    on_disk = {p.stem for p in NORMS_DIR.glob('*.md') if p.name != 'CONTEXT.md'}
    assert declared == on_disk, (
        f'declared but missing: {sorted(declared - on_disk)}; '
        f'on disk but undeclared: {sorted(on_disk - declared)}')


def test_a_norm_declares_its_name_and_what_obeying_it_buys():
    """core/SCHEMA-layers.md § Layer: norm — `name` matches the filename, `description` is one line."""
    broken = []
    for path in sorted(NORMS_DIR.glob('*.md')):
        if path.name == 'CONTEXT.md':
            continue
        m = FRONTMATTER.match(path.read_text(encoding='utf-8'))
        if not m:
            broken.append(f'{path.name}: no name/description frontmatter')
        elif m.group(1) != path.stem:
            broken.append(f'{path.name}: declares name {m.group(1)!r}')
    assert not broken, '\n  '.join(broken)


def test_the_always_loaded_block_matches_its_sources():
    """The round-trip: what AGENTS.md carries is exactly what the norm files say, in registry order.

    Asserted on the CHECKED-IN file, not on a regenerated copy — a generator compared against its
    own output agrees with itself no matter how wrong both are. This is the only check that fails
    when someone edits the rules straight into AGENTS.md, which is the way they were edited for as
    long as the file has existed.
    """
    text = AGENTS.read_text(encoding='utf-8')
    head, _, rest = text.partition(norms.START)
    body, _, _ = rest.partition(norms.END)
    live = [b.strip() for b in ('\n' + body.strip()).split('\n- ')[1:]]
    assert live == [text for _, text in norms.published()], (
        'AGENTS.md and core/norms/ disagree — run core/hooks/routing/norms.py')
    assert norms.START in text and norms.END in text


def test_a_norm_is_a_rule_and_not_an_essay():
    """One bullet, no blank line inside it: a norm that grew a second paragraph is a SPECS section.

    The cap is the point of the layer. Every line here is loaded by every session in the workspace,
    so the cost of a norm growing is paid forever and silently — the same shape as the read
    amplification measured on ROADMAP.md, one level closer to the prompt.
    """
    fat = [name for name, text in norms.published() if '\n\n' in text]
    assert not fat, (
        f'these norms carry more than one rule: {fat}. Move the rationale to the SPECS.md that '
        f'owns the rule and leave a pointer')


def test_switching_a_norm_off_removes_it_from_the_prompt():
    """The group's honesty check (core/SPECS.md § AD-14).

    Run in a subprocess: `feature_law` caches nothing, but the switch is read from the environment
    at call time, and asserting it in-process would prove only that this test can set a variable.
    A norm is markdown and calls no function, so publishing is the whole meaning of "on" — exactly
    the skills group's argument, with a stronger observable because AGENTS.md is always loaded.
    """
    name = _rows()[0]['name']
    script = ('import sys; sys.path.insert(0, "core/hooks/routing"); import norms; '
              'print(",".join(s for s, _ in norms.published()))')
    both = {}
    for label, env in (('on', {}), ('off', {law.OFF_ENV: name})):
        out = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True,
                             cwd=WORKSPACE_ROOT, env={**os.environ, **env}, encoding='utf-8')
        assert out.returncode == 0, out.stderr
        both[label] = out.stdout.strip().split(',')
    assert name in both['on'], f'{name} is not published even switched on'
    assert name not in both['off'], (
        f'{name} still publishes under {law.OFF_ENV}: the row names the generator but the switch '
        f'changes nothing there')
    assert len(both['off']) == len(both['on']) - 1, 'the switch must remove one rule, not all of them'
