# T1 the workspace's health reading: the findings behind the summary layer, and the grid that draws
# them. Zero-token, no network, no browser.
#
# WHAT THESE GUARD, and it is a different question from test_diagram.py's. That file asks whether
# the picture can be more wrong than its sources. These ask whether a number the page presents as a
# PROBLEM actually is one — because the summary's whole value is that its findings can be believed
# without checking them, and the first version of this list opened with a number that was not a
# defect at all.
import subprocess

import diagram_data as data
import diagram_fanin as fanin_form
import diagram_health as health
import diagram_overview as overview_form
import feature_law as law
from conftest import WORKSPACE_ROOT
from platform_law import interpreter

TOOL = WORKSPACE_ROOT / 'core/tools/wos/diagram/architecture'


def _grids(rows: list) -> tuple:
    """The two halves the page draws, in the order it draws them."""
    return health.by_layer(rows, 'automatic'), health.by_layer(rows, 'on-demand')


def test_the_summary_counts_the_same_workspace_the_matrix_does():
    """One source of truth. The summary aggregates the matrix's own rows rather than counting the
    registry a second time — two counts of one thing are free to disagree, and the day they do the
    page contradicts itself in the two places a reader compares first."""
    rows, _columns, _cells = data.matrix(data.features())
    layered = sum(total for _layer, _strength, total in health.by_layer(rows))
    assert layered == sum(len(law.groups(row)) for row in rows)
    assert {layer for layer, _s, _t in health.by_layer(rows)} == law.GROUPS


def test_the_two_halves_of_the_split_lose_nothing_between_them():
    """The grid is drawn once per `runs` value, and the split has to be a partition. A feature in
    neither half vanishes from the page's first screen; one in both inflates the enforcement story
    with features that never enforce."""
    rows, _columns, _cells = data.matrix(data.features())
    halves = sum(total for value in law.RUNS for _l, _s, total in health.by_layer(rows, value))
    assert halves == sum(total for _l, _s, total in health.by_layer(rows))


def test_a_declared_layer_holding_nothing_is_still_drawn():
    """`agents` and `flows` are declared layers with no feature in them. A grid built from what
    exists cannot show what does not, so the rows come from the declared set."""
    rows, _columns, _cells = data.matrix(data.features())
    empty = [layer for layer, _s, total in health.by_layer(rows) if not total]
    assert empty, 'expected at least one declared-but-unbuilt layer'
    html = overview_form.render(*_grids(rows), [])
    for layer in empty:
        assert layer in html


def test_a_harness_mirror_is_excluded_by_rule_not_by_a_list():
    """A provider's mirrored tree is not this workspace's rot to fix. The rule is "top-level dotted
    directory", so a harness nobody has heard of yet is covered the day it lands — a hardcoded list
    would start reporting it as an orphan instead."""
    assert health.harness_owned('.some-future-harness/skills')
    assert not health.harness_owned('core/tools/wos')
    assert not any(d.startswith('.') for d, _n in health.orphans())


def test_every_finding_is_a_gap_rather_than_a_shape():
    """The regression for the mistake this list was born with. "28 of 68 features enforce nothing"
    counted 15 skills, 7 tools and 6 recording hooks — features that wait to be called instead of
    pushing — and reported the capability half of the workspace as dead weight. A findings list
    whose biggest number is not a problem teaches its reader to stop believing the rest of it."""
    rows, _columns, _cells = data.matrix(data.features())
    _nodes, _edges, coverage = data.containment()
    texts = ' '.join(f['text'] for f in health.findings(rows, coverage))
    assert 'enforce nothing' not in texts
    assert 'exactly one feature' not in texts


def test_every_finding_carries_a_target_and_says_when_nobody_set_one():
    """A count with no target cannot read as good or bad, which is how this list once opened with a
    number that was not a defect at all. Replaced the `inferred` check on 2026-08-18: the firing
    moment stopped being guessed from directory convention that day (core/hooks/trigger/trigger_law.py), so
    the region this file used to guard for honest labelling is now simply declared.

    An UNDECIDED target must print as undecided. Rendering nothing would let it pass for a met one,
    which is the same silence the column exists to break.
    """
    rows, _columns, _cells = data.matrix(data.features())
    _nodes, _edges, coverage = data.containment()
    items = health.findings(rows, coverage)
    assert all('target' in f for f in items)
    assert any(f['target'] is None for f in items), 'the undecided target is itself a finding'
    assert 'undecided' in overview_form.render(*_grids(rows), items)


def test_the_fan_in_reaches_every_feature_the_matrix_does():
    """The fan-in is the matrix's own relation re-read, so it must hold the same features.

    A feature spanning layers is at two points on purpose — `latex` is a gate and the tool family
    that gate calls — so the pair count is checked against the declared paths rather than against
    the row count, and both grains are checked: the directory grain collapses two paths in one
    directory, and only set membership can be asserted of it.
    """
    rows = data.features()
    for grain in ('path', 'area'):
        points, dangling = data.fan_in(rows, grain)
        seen = {name for _point, names in points for name in names}
        assert seen | set(dangling) == law.names(), (
            f'the {grain} fan-in loses {sorted(law.names() - seen - set(dangling))}')
    points, dangling = data.fan_in(rows)
    assert sum(len(names) for _p, names in points) == sum(len(r['wired_paths']) for r in rows)
    assert dangling == [row['name'] for row in data.unwired(rows)]


def test_the_collapsed_tail_hides_no_point():
    """The 43 one-to-one points are collapsed to a count, which is only honest if the count is
    right. A collapse that silently dropped a point would make the drawing say the workspace is
    more concentrated than it is — the exact claim this view exists to make."""
    points, dangling = data.fan_in(data.features())
    hubs, tail = fanin_form._split(points)
    assert len(hubs) + tail == len(points)
    assert all(len(names) >= fanin_form.HUB_MIN for _p, names in hubs)
    assert str(tail) in fanin_form.render_graph(points, dangling)


def test_the_summary_needs_no_click(tmp_path):
    """The page's whole defect was that its two most-asked questions were behind detail. The
    summary, the sequence and all three fan-in shapes render outside the tab strip, so they are on
    screen before any interaction — the fan-in shapes especially, since Lucas cuts two of the three
    by looking at them and a shape behind a click does not get looked at."""
    out = tmp_path / 'ARCHITECTURE.html'
    result = subprocess.run([interpreter(), str(TOOL), '--out', str(out)], capture_output=True, text=True,
                            cwd=WORKSPACE_ROOT, encoding='utf-8')
    assert result.returncode == 0, result.stdout + result.stderr
    html = out.read_text(encoding='utf-8')
    tabs = html.index('<div class="tabs">')
    assert html.index('class="heat"') < tabs
    assert html.index('class="fanin"') < tabs
    assert html.count('class="fbars"') == 2 and html.index('class="fbars"') < tabs
