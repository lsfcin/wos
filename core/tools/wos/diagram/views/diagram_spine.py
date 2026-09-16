# The routing spine: which directory routes to which, drawn from the auto-synced routing blocks.
#
# Node-link here and nowhere else, because this is the one relation in the workspace that is a
# shallow tree — an agent walks it from the root, one hop per level, and path following is the
# task node-link drawings win. Depth is capped: the picture answers "where do I go next", and the
# whole tree at once is the hairball the cap exists to prevent.
from html import escape

ROW = 22          # vertical pitch, one row per node — an indented tree read as a drawing
INDENT = 26       # horizontal pitch per level: an indent, not a gap. A wider one turns
                  # every connector into a long horizontal rule and the tree reads as a table.
PAD = 14
LABEL_DY = 4


def _children(edges: list) -> dict:
    out: dict = {}
    for parent, child in edges:
        out.setdefault(parent, []).append(child)
    return {k: sorted(set(v)) for k, v in out.items()}


def _walk(children: dict, node: str, depth: int, max_depth: int, rows: list) -> None:
    """Depth-first, alphabetical, one row per node. Deterministic by construction: the same tree
    renders byte-identically, which is what lets --check compare the file instead of a timestamp."""
    rows.append((node, depth))
    if depth >= max_depth:
        return
    for child in children.get(node, []):
        _walk(children, child, depth + 1, max_depth, rows)


def render(nodes: dict, edges: list, max_depth: int = 3) -> str:
    children = _children(edges)
    rows: list = []
    _walk(children, '', 0, max_depth, rows)
    index = {node: i for i, (node, _d) in enumerate(rows)}
    width = PAD * 2 + INDENT * (max_depth + 1) + _widest(rows)
    height = PAD * 2 + ROW * max(len(rows), 1)

    lines = [f'<svg class="spine" viewBox="0 0 {width} {height}" width="{width}" '
             f'height="{height}" role="img" aria-label="routing spine">']
    for node, depth in rows:
        if not node:
            continue
        parent = node.rsplit('/', 1)[0] if '/' in node else ''
        if parent not in index:
            continue
        lines.append(_elbow(index[parent], index[node], depth))
    for node, depth in rows:
        lines.append(_node(node, depth, index[node], node in children and depth == max_depth))
    lines.append('</svg>')
    hidden = len(nodes) - len(rows)
    if hidden > 0:
        lines.append(f'<p class="note">{hidden} directories sit deeper than level {max_depth} and '
                     f'are not drawn. They are reached by the same chain, one hop at a time — '
                     f'which is the point of the spine rather than a gap in it.</p>')
    return '\n'.join(lines)


def _widest(rows: list) -> int:
    """Room for the longest label at its own depth. Approximate on purpose — the SVG scrolls, and
    a measured font metric would need a browser the generator does not have."""
    return max((len(node.rsplit('/', 1)[-1]) * 7 for node, _d in rows), default=40) + 30


def _elbow(parent_row: int, child_row: int, depth: int) -> str:
    x0 = PAD + INDENT * (depth - 1)
    x1 = PAD + INDENT * depth
    y0 = PAD + ROW * parent_row + ROW // 2
    y1 = PAD + ROW * child_row + ROW // 2
    return f'<path class="link" d="M{x0} {y0} V{y1} H{x1}" />'


def _node(node: str, depth: int, row: int, truncated: bool) -> str:
    x = PAD + INDENT * depth
    y = PAD + ROW * row + ROW // 2
    name = node.rsplit('/', 1)[-1] if node else '/'
    suffix = ' …' if truncated else ''
    title = escape(node or '(workspace root)')
    return (f'<g class="node d{depth}"><title>{title}</title>'
            f'<circle cx="{x}" cy="{y}" r="3.5" />'
            f'<text x="{x + 9}" y="{y + LABEL_DY}">{escape(name)}{suffix}</text></g>')


def legend(coverage: dict) -> str:
    return ('<p class="note">Every edge is read from a generated routing block — the same table an '
            'agent follows. Nothing here is drawn by hand, so a wrong edge is a wrong routing '
            'table, and fixing the picture means fixing the source. '
            f'Parsed {coverage["parsed"]} of {coverage["total"]} blocks.</p>')
