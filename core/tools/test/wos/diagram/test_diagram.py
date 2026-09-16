# T1 the workspace picture: the generator behind ARCHITECTURE.html.
# Zero-token, no network, no browser.
#
# WHAT THESE GUARD, and it is not "does it draw something pretty": the picture's whole claim is
# that it cannot be more wrong than its sources. That claim dies two ways — a source silently
# dropped, so the drawing looks complete while a subtree is missing, and an inferred edge drawn
# like a declared one. Both are checked here. A drawing nobody can trust is worse than none,
# because it is believed.
import os
import subprocess

import diagram_data as data
import diagram_health as health
import diagram_matrix as matrix_form
import diagram_overview as overview_form
import diagram_spine as spine_form
import diagram_treemap as mass_form
import feature_law as law
import tool_law
from conftest import WORKSPACE_ROOT
from platform_law import interpreter

TOOL = WORKSPACE_ROOT / 'core/tools/wos/diagram/architecture'


def _run(*args, off=''):
    # Inherited, with only the switch overridden: a replaced environment loses the variables the
    # interpreter needs to start on some systems, which reads as the feature switch failing.
    env = {**os.environ, law.OFF_ENV: off} if off else None
    return subprocess.run([interpreter(), str(TOOL), *args], capture_output=True, text=True,
                          cwd=WORKSPACE_ROOT, env=env, encoding='utf-8')


def _page(tmp_path):
    out = tmp_path / 'ARCHITECTURE.html'
    result = _run('--out', str(out))
    assert result.returncode == 0, result.stdout + result.stderr
    return out.read_text(encoding='utf-8'), result.stdout


def test_every_declared_feature_reaches_the_matrix():
    """Nothing is silently dropped. A feature missing from the picture is invisible exactly where
    the picture is supposed to make it visible, which is how a diagram starts lying."""
    rows, _columns, _cells = data.matrix(data.features())
    assert {row['name'] for row in rows} == law.names()


def test_an_unwired_feature_is_shown_rather_than_omitted():
    """`features --findings` counts what cannot be switched off; a drawing of wiring would hide
    those rows by construction, so it marks them instead."""
    rows, columns, cells = data.matrix(data.features())
    html = matrix_form.render(rows, columns, cells, data.trigger_of)
    for row in data.unwired(rows):
        assert row['name'] in html
    assert 'unwired' in html


def test_coverage_names_a_block_it_could_not_read(tmp_path):
    """Fail-loud, not fail-quiet: a routing block without its sentinels is COUNTED and NAMED."""
    root = tmp_path / 'ws'
    (root / 'sub').mkdir(parents=True)
    (root / 'AGENTS.md').write_text('# root\n<!-- routing:start -->\n'
                                    '| [`sub/`](sub/CONTEXT.md) | a subtree |\n'
                                    '<!-- routing:end -->\n', encoding='utf-8', newline='\n')
    (root / 'sub/CONTEXT.md').write_text('# sub\n> no routing block at all\n', encoding='utf-8', newline='\n')
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=root, check=True)

    _nodes, edges, coverage = data.containment(root)
    assert coverage['total'] == 2 and coverage['parsed'] == 1
    assert coverage['unparsed'] == ['sub/CONTEXT.md']
    assert ('', 'sub') in edges


def test_nothing_on_the_page_is_guessed_at(tmp_path):
    """The registry landed, and this is the change its predecessor asked for by name.

    *When a hook fires* was the page's last inferred edge, guessed from directory convention until
    trigger_law.py began reading it out of the registrations — so the assertion flips: the firing
    moment is now READ, and what the registrations cannot place is counted as a gap rather than
    guessed at. The page still carries the word, because the footer states what it inferred, and
    stating "nothing" is the honest form of that claim.

    THE SECOND VALUE IS `declared`, NOT `inferred`, and reading it as the opposite is how this case
    passed for a week on a broken walk. `trigger_of` returns `bool(moments)`; the name here said
    the reverse, so `assert not inferred` demanded that this site have NO moment — which is exactly
    what a launcher-relative spawn produced (core/hooks/trigger/hook_reach.py § target). The test
    asserted the opposite of its own docstring and went green on the defect it was written to
    forbid. Fixed 2026-09-05 with the walk.
    """
    when, declared = data.trigger_of('core/hooks/checks')
    assert declared and when != 'not declared', (
        'a firing moment is being guessed again — trigger_law.py reads it from the registrations')
    html, _out = _page(tmp_path)
    assert 'inferred' in html


def test_the_page_carries_everything_it_needs(tmp_path):
    """Self-contained or it is not an asset inside the workspace: it opens from a file:// path on a
    machine with no network, under any provider."""
    html, _out = _page(tmp_path)
    for offender in ('http://', 'https://', '<script', 'src=', '<link'):
        assert offender not in html
    assert html.startswith('<!-- ARCHITECTURE.html — generated by')


def test_the_output_is_deterministic(tmp_path):
    """--check compares the file, so a timestamp or a commit sha in the page would make every
    session close report a stale picture and commit a diff that means nothing."""
    first, _out = _page(tmp_path)
    second, _out = _page(tmp_path)
    assert first == second


def test_check_reports_stale_and_current(tmp_path):
    out = tmp_path / 'ARCHITECTURE.html'
    assert _run('--out', str(out), '--check').returncode == 1       # absent is stale
    _page(tmp_path)
    assert _run('--out', str(out), '--check').returncode == 0
    out.write_text(out.read_text(encoding='utf-8') + '<!-- hand edit -->', encoding='utf-8', newline='\n')
    stale = _run('--out', str(out), '--check')
    assert stale.returncode == 1 and 'STALE' in stale.stdout


def test_the_switch_is_honest(tmp_path):
    """core/SPECS.md § AD-14: the row claims a switch, so throwing it must move the observable.
    Off means no picture written and the tool's own refusal code — not a quiet exit 0 that an
    ablation arm would read as success."""
    out = tmp_path / 'off.html'
    result = _run('--out', str(out), off='diagram')
    assert result.returncode == tool_law.OFF_EXIT and not out.exists()


def test_the_treemap_tiles_its_whole_area():
    """A squarify bug shows up as blank canvas, which reads as 'nothing is there' rather than as a
    drawing error — the one failure mode of this form that a viewer cannot spot."""
    rows = [r for r in data.mass() if r[2] > 0]
    rects = mass_form._layout([size for _n, _f, size in rows], 0, 0,
                              mass_form.WIDTH, mass_form.HEIGHT)
    assert len(rects) == len(rows)
    covered = sum(w * h for _x, _y, w, h in rects)
    assert abs(covered - mass_form.WIDTH * mass_form.HEIGHT) < 1


def test_the_spine_stops_at_its_depth_and_says_so():
    """Overview first: the whole tree at once is the hairball the cap exists to prevent, and a cap
    that hides what it cut is the same lie as dropping a node."""
    nodes, edges, _coverage = data.containment()
    html = spine_form.render(nodes, edges, max_depth=1)
    assert 'sit deeper than level 1' in html
