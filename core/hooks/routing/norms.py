#!/usr/bin/env python3
# Publish core/norms/*.md into AGENTS.md's rule block, in the registry's order.
#
# The `norms` group's one wiring point (core/SPECS.md § AD-14), the same shape as the skills
# mirror: a norm is markdown and calls no function, so its only real "off" is the publisher
# declining to publish it. Here that is stronger than for a skill — AGENTS.md is always
# loaded, so a switched-off norm leaves the session's prompt entirely rather than merely
# going uninvoked. That is the observable the ablation needs to price always-loaded context.
#
# ORDER COMES FROM core/features.txt, never from this directory's listing. Order matters in a
# prompt, and a second ordered list is the asymmetry this workspace keeps paying for; the
# registry is already ordered, already the instrument, so it is the one list.
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402

NORMS_DIR = feature_law.CORE / 'norms'
AGENTS_FILE = feature_law.CORE.parent / 'AGENTS.md'
START = '<!-- norms:start -->'
END = '<!-- norms:end -->'
FRONTMATTER = re.compile(r'\A---\n.*?\n---\n', re.DOTALL)


def body(path: Path) -> str:
    """The published rule: everything after the frontmatter, stripped.

    The body IS the bullet as it appears in AGENTS.md — no rendering, no wrapping. A norm
    that needs a paragraph of rationale is a SPECS.md section with a pointer, not a longer
    norm, because every line here is paid by every session in the workspace.
    """
    return FRONTMATTER.sub('', path.read_text(encoding='utf-8')).strip()


def published() -> list:
    """Every switched-on norm, in registry order, as (name, body).

    A row naming a file that does not exist is skipped rather than raised: `is_enabled`
    fails open on purpose, and the publisher inherits that stance — a bad line of data must
    never cost the workspace the other nine rules.
    """
    out = []
    for row in feature_law.load_registry():
        if 'norms' not in feature_law.groups(row) or not feature_law.is_enabled(row['name']):
            continue
        path = NORMS_DIR / f"{row['name']}.md"
        if path.is_file():
            out.append((row['name'], body(path)))
    return out


def block() -> str:
    rules = '\n'.join(f'- {text}' for _, text in published())
    return f'{START}\n{rules}\n{END}'


def sync() -> int:
    text = AGENTS_FILE.read_text(encoding='utf-8')
    if START not in text or END not in text:
        print(f'{AGENTS_FILE}: no norms block to fill', file=sys.stderr)
        return 1
    head, _, rest = text.partition(START)
    _, _, tail = rest.partition(END)
    new = head + block() + tail
    if new != text:
        AGENTS_FILE.write_text(new, encoding='utf-8', newline='\n')
        print(f'✓ norms-sync: {AGENTS_FILE.name} ({len(published())} rules)')
    return 0


if __name__ == '__main__':
    raise SystemExit(sync())
