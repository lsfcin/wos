# The enforcement matrix: every declared feature against every site that enforces it.
#
# A grid rather than a node-link graph, and that is a measured choice rather than a taste: past a
# few dozen nodes a matrix beats a node-link drawing on every readability task except path
# following (core/refs/REFS.md § Tooling). This workspace declares 67 features
# across 23 sites, which is well past the crossover — a graph of it is a hairball.
from html import escape

# One mark per enforcement strength, ordered hardest first. The mark is the reading: a column of
# filled squares is a wall, a column of rings is advice, and the difference is visible before any
# label is read.
MARKS = {
    'blocks': ('■', 'blocks the commit'),
    'warns': ('▲', 'warns, never blocks'),
    'generates': ('●', 'writes a file'),
    'advises': ('○', 'advice to the agent'),
    'none': ('·', 'wired, enforces nothing'),
}


def _column_label(area: str) -> str:
    """`hooks/checks`, not `checks`. Every site but one lives under core/, so that prefix is the
    one segment carrying no information — and dropping the segment ABOVE the leaf instead would
    leave `skills` and `wos` sitting next to each other with nothing to tell them apart."""
    return area[len('core/'):] if area.startswith('core/') else area


def render(rows: list, columns: list, cells: dict, trigger_of) -> str:
    """The matrix as an HTML table. Rows are grouped by the tree layer they belong to, because
    that grouping is itself declared (core/features.txt § group) rather than invented here."""
    out = ['<table class="matrix">', '<thead><tr><th class="rowhead">feature</th>']
    for area in columns:
        when, declared = trigger_of(area)
        mark = '' if declared else ' <span class="inf">no moment</span>'
        out.append(f'<th title="{escape(area)} — fires: {escape(when)}">'
                   f'<span class="vert">{escape(_column_label(area))}</span>{mark}</th>')
    out.append('</tr></thead><tbody>')

    group = None
    for row in rows:
        if row['group'] != group:
            group = row['group']
            out.append(f'<tr class="grouprow"><td colspan="{len(columns) + 1}">{escape(group)}'
                       f'</td></tr>')
        out.append(_row(row, columns, cells))
    out.append('</tbody></table>')
    return '\n'.join(out)


def _row(row: dict, columns: list, cells: dict) -> str:
    name = row['name']
    label = escape(name) if row['areas'] else f'{escape(name)} <span class="unwired">unwired</span>'
    tds = [f'<th class="rowhead" title="{escape(row.get("description", ""))}">{label}</th>']
    for area in columns:
        strength = cells.get((name, area))
        if strength is None:
            tds.append('<td class="empty"></td>')
            continue
        mark, meaning = MARKS.get(strength, ('?', strength))
        tds.append(f'<td class="{escape(strength)}" title="{escape(name)} at {escape(area)} — '
                   f'{escape(meaning)}">{mark}</td>')
    return '<tr>' + ''.join(tds) + '</tr>'


def legend() -> str:
    items = ''.join(f'<span class="key"><b>{mark}</b> {escape(meaning)}</span>'
                    for mark, meaning in MARKS.values())
    return (f'<p class="legend">{items}</p>'
            '<p class="note">Rows and columns both come from <code>core/features.txt</code>. '
            'An empty column is a site that enforces nothing — a finding about the workspace, '
            'not about the drawing. Column tooltips carry the firing moment, read from the '
            'registrations themselves by <code>core/hooks/trigger/trigger_law.py</code>; a site marked '
            '<span class="inf">no moment</span> is one nothing in this repo registers.</p>')
