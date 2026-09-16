#!/usr/bin/env python3
# tex-interface-gen.py: Generate .texif interfaces, labels.md, and bib/review checks.
#
# Usage:
#   tex-interface-gen.py <file.tex>             — generate <stem>.texif + regenerate labels.md
#   tex-interface-gen.py --bib-check <file.bib> — warn about missing refs/*.yaml files

from __future__ import annotations
import re, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_law import rel as _rel  # noqa: E402
from tex_interface_parser import parse_tex, find_paper_root  # noqa: E402


def write_interface(tex_path: Path, data: dict, paper_root: Path | None) -> Path:
    out_path = tex_path.with_suffix('.texif')
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    rel = _rel(tex_path, paper_root) if paper_root else tex_path.name
    lines = [
        f'<!-- INTERFACE: {rel} | LOC: {data["loc"]} | ~{data["words"]} words | {ts} -->',
        '<!-- Auto-generated — do not edit. Regenerated on every save of the source. -->',
    ]
    events = sorted(
        [(s['line'], 'struct', s) for s in data['struct_points']] +
        [(c['line'], c['kind'], c['data']) for c in data['content_items']],
        key=lambda x: x[0],
    )
    openings = data['openings']

    def render(lnum: int, kind: str, d: dict) -> list[str]:
        if kind == 'equation':
            lbl = f'`{d["label"]}`' if d['label'] else '*(unlabelled)*'
            return [f'`equation` [line {lnum}] {lbl}', '```latex', d['content'].strip(), '```']
        if kind in ('figure', 'table'):
            lbl = f'`{d["label"]}`' if d['label'] else '*(unlabelled)*'
            cap = f'"{d["caption"]}"' if d['caption'] else '*(no caption)*'
            return [f'`{kind}` [line {lnum}] {lbl} — {cap}']
        if kind == 'listing':
            lbl = f'`{d["label"]}`' if d['label'] else '*(unlabelled)*'
            cap = f'"{d["caption"]}"' if d['caption'] else '*(no caption)*'
            lang = d['lang'] or 'text'
            out = [f'`listing` [line {lnum}] {lbl} · {lang} · {d["loc"]} lines — {cap}']
            if d['preview']:
                out += [f'```{lang}'] + d['preview'] + ['```']
            return out
        return []

    for lnum, kind, d in events:
        if kind == 'struct':
            lines += ['', '#' * d['level'] + ' ' + d['title']]
            if snippet := openings.get((d['level'], d['title'])):
                lines.append(f'*"{snippet}"*')
        else:
            lines.extend(render(lnum, kind, d))

    if data['inputs']:
        lines += ['\n---', '\n## Inputs'] + [f'- `{i["path"]}` [line {i["line"]}]' for i in data['inputs']]
    if data['citations']:
        cites = ' · '.join(f'`{k}`' for k in sorted(data['citations']))
        lines += ['\n---', f'\n## Citations\n\n{cites}']
    if data['todos']:
        lines += ['\n---', '\n## TODOs'] + [f'- [line {t["line"]}] {t["text"]}' for t in data['todos']]

    out_path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    return out_path


def check_relationships(data: dict, paper_root: Path) -> None:
    if not data['citations'] or not (paper_root / 'refs').exists():
        return
    missing = []
    for key in sorted(data['citations']):
        yp = paper_root / 'refs' / f'{key}.yaml'
        if yp.exists():
            txt = yp.read_text(encoding='utf-8', errors='ignore')
            if not re.search(r'relevance:\s*".{5,}"', txt):
                missing.append(key)
    if missing:
        print(f'💬 RELEVANCE: add/update relevance field in {len(missing)} ref(s):')
        for k in missing:
            print(f'   refs/{k}.yaml → relevance: "..."')


def regenerate_labels(paper_root: Path) -> None:
    tex_files = sorted(f for f in paper_root.rglob('*.tex') if 'build' not in str(f))
    all_def, all_used = [], []
    for tf in tex_files:
        try:
            d = parse_tex(tf)
        except Exception:
            continue
        rel = _rel(tf, paper_root)
        all_def += [{**lbl, 'file': rel} for lbl in d['defined_labels']]
        all_used += [{**ref, 'file': rel} for ref in d['used_refs']]
    defined_set = {e['label'] for e in all_def}
    dangling = [u for u in all_used if u['ref'] not in defined_set]
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    out = [
        '# labels — cross-file label registry',
        f'> Auto-generated {ts} — do not edit.',
        '', '## Defined Labels', '',
        f'{"Label":<40} {"Type":<12} {"File":<50} Line',
        '─' * 110,
    ]
    for e in sorted(all_def, key=lambda x: x['label']):
        out.append(f'{e["label"]:<40} {e["type"]:<12} {e["file"]:<50} {e["line"]}')
    out.append('')
    if dangling:
        ref_hdr = r'\ref{...}'
        out += [f'## Dangling References ({len(dangling)} issues) ⚠', '',
                f'{ref_hdr:<40} {"Used in":<50} Line', '─' * 100]
        for dr in sorted(dangling, key=lambda x: x['ref']):
            out.append(f'{dr["ref"]:<40} {dr["file"]:<50} {dr["line"]}')
    else:
        out += ['## Dangling References (0 issues)', '', r'All \ref{} usages resolved.']
    (paper_root / 'labels.md').write_text('\n'.join(out) + '\n', encoding='utf-8', newline='\n')
    print('✓ labels.md updated')


def bib_check(bib_path: Path) -> None:
    keys = re.findall(r'^@\w+\{(\w+),', bib_path.read_text(encoding='utf-8', errors='ignore'), re.MULTILINE)
    root = find_paper_root(bib_path)
    if not root:
        return
    refs_dir = root / 'refs'
    if not refs_dir.exists():
        print(f'💬 REFS: refs/ directory missing at {refs_dir}')
        return
    missing = [k for k in keys if not (refs_dir / f'{k}.yaml').exists()]
    if missing:
        print(f'💬 REFS MISSING ({len(missing)}) — create ref files:')
        for k in missing:
            print(f'   {k}  →  refs/{k}.yaml')
    else:
        print(f'✓ refs: all {len(keys)} bib entries have ref files')


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print('Usage: tex-interface-gen.py <file.tex> | --bib-check <file.bib>', file=sys.stderr)
        return 1
    if args[0] == '--bib-check':
        if len(args) < 2:
            print('--bib-check requires a .bib path', file=sys.stderr)
            return 1
        bib_check(Path(args[1]))
        return 0
    tex_path = Path(args[0])
    if not tex_path.exists() or tex_path.suffix != '.tex':
        return 0
    root = find_paper_root(tex_path)
    try:
        data = parse_tex(tex_path)
        out = write_interface(tex_path, data, root)
        print(f'✓ .texif: {out}')
    except Exception as e:
        print(f'⚠ tex-interface-gen: {tex_path}: {e}', file=sys.stderr)
        return 1
    if root:
        if not (root / 'refs' / 'CONTEXT.md').exists():
            print(f'💬 SCAFFOLD: refs/CONTEXT.md missing — run:')
            print(f'   python3 {Path(__file__).parent}/paper-scaffold.py adapt {root}')
        try:
            regenerate_labels(root)
        except Exception as e:
            print(f'⚠ labels.md: {e}', file=sys.stderr)
        try:
            check_relationships(data, root)
        except Exception as e:
            print(f'⚠ relationships check: {e}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
