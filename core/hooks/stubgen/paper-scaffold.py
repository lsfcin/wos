#!/usr/bin/env python3
# paper-scaffold.py: Initialize or adapt a paper directory to workspace standards.
#   new <name>    — create academy/papers/<name>/ from template
#   adapt <path>  — add missing scaffold files to an existing paper
# Both modes are safe: existing files are never overwritten (skipped with ~).
from __future__ import annotations
import re
import sys
from pathlib import Path

PAPERS = Path(__file__).resolve().parents[2] / 'academy' / 'papers'
_dir_to_title = lambda s: re.sub(r'^\d{4}-[^-]+-', '', s).replace('_', ' ').title()
RS, RE = '<!-- routing:start -->', '<!-- routing:end -->'
ROUTE = f'{RS}\n## Routing\n\n{RE}\n'


def _refs_ctx(name: str) -> str:
    return f"""# References
> Curated reference analyses for {name} — one YAML per bib entry in lib/refs.bib.
> Level-2 promoted refs (structured). Level-1 raw capture goes in REFS.md — see /inbox refs convention.

## Schema

```yaml
key: <bib-key>
type: article | book | conference | preprint | thesis
year: <year>
venue: "<journal or conference>"
url: "<DOI or canonical link>"
citations: <count or "~N">
contributions:
  - <one bullet per distinct claim>
gaps:
  - <limitation relevant to this work>
tags: [<role-first>, <metric>, <method>, <platform>]
relevance: "<how this reference relates to this manuscript>"
notes: ~  # cross-paper lineage, group connections, anything cross-file
```

## Tag Categories

Tags are a flat list. Always put role tags first; add domain-specific tags after.

| Category | Values |
|----------|--------|
| **Role** (1–2, always first) | `foundational` · `survey` · `competing-work` · `baseline` · `ground-truth` · `method-source` · `tool` · `application` |
| **Domain** | ← add paper-specific domain tags here (e.g. method names, platforms, metrics) |

`baseline` = directly compared against in experiments; `competing-work` = same problem space, no direct benchmark.
Add a `## Domain Tags` section below with the specific values for this paper once the domain is clear.

Use `notes` for cross-paper prose. No need to update both files when noting a connection — write it in whichever file you are editing.

## Workflow

- Read a review before making claims about a paper in the manuscript.
- Create or update `refs/<key>.yaml` when you add `\\cite{{key}}` to a section.
- The `post-edit` hook warns about missing review files when `lib/refs.bib` is edited.
- The hook warns when `relevance:` is empty or missing after a `.tex` save.

{ROUTE}"""


def _sections_ctx() -> str:
    return f"""# Sections
> Source files for each manuscript section (200 LOC limit per file)

**Interface enforcement:** Every `.tex` file has a `.texif` sibling (auto-generated).
Read the `.texif` before reading or editing a section — the pre-read hook enforces this.
See `labels.md` at the paper root for the cross-file label registry.

{ROUTE}"""


def _paper_ctx(name: str, dir_name: str) -> str:
    return f"""# {name}
> ← add one-line description

TODO: brief summary — contribution, target venue, status.

## Build

```bash
cd academy/papers/{dir_name}
latexmk -xelatex -halt-on-error -interaction=nonstopmode main.tex
```

Clean rebuild: `latexmk -C && latexmk -xelatex -halt-on-error -interaction=nonstopmode main.tex`

{ROUTE}"""


def _main_tex(name: str) -> str:
    return f"""% Main document: orchestration only — preamble, section inputs, bibliography.
\\documentclass{{article}}
\\usepackage{{amsmath,amssymb,graphicx,hyperref}}

\\title{{{name}}}
\\author{{TODO}}

\\begin{{document}}
\\maketitle

\\input{{sections/01_introduction}}

% \\bibliography{{lib/refs}}
\\end{{document}}
"""


_LATEXMKRC = '$pdf_mode = 5;\n$out_dir = ".";\n$aux_dir = "build";\n'
_GITIGNORE = 'build/\nmain.pdf\n*.synctex.gz\n*.fls\n*.fdb_latexmk\n*.aux\n*.log\n'
# Line 2 is hoisted into the parent's routing row: a placeholder renders as "—" and the
# parent stops being navigable. These dirs are known by name — never placeholder them.
_SUB_DESC = {'lib': 'LaTeX includes for this paper — bibliography, macros, and style files.',
             'images': 'Figures for this paper — source assets and exported plots used by sections/.',
             'tables': 'Tables for this paper — generated .tex fragments included by sections/.'}
_SUB_CTX = lambda d: f'# {d.title()}\n> {_SUB_DESC.get(d, "← add description")}\n\n{ROUTE}'


def _terms_yaml() -> str:
    return """\
# terms.yaml — canonical terminology for this paper.
# Run: Core/tools/paper/terms <paper-path>
# Each key is the CORRECT form. The list is wrong forms to flag.
# The pre-commit hook runs this scan and warns on deviations.
#
# Example:
#   real-time:
#     - real time
#     - realtime
#     - near-real-time
#
canonical: {}  # ← replace {} with your term definitions
"""


def scaffold(root: Path, name: str, dir_name: str, is_new: bool) -> None:
    created: list[str] = []
    skipped: list[str] = []

    def put(rel: str, content: str) -> None:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            skipped.append(rel)
        else:
            p.write_text(content, encoding='utf-8', newline='\n')
            created.append(rel)

    if is_new:
        put('main.tex', _main_tex(name))
        put('.latexmkrc', _LATEXMKRC)
        put('.gitignore', _GITIGNORE)

    put('CONTEXT.md', _paper_ctx(name, dir_name))
    put('labels.md', '# labels — cross-file label registry\n> Auto-generated by tex-interface-gen.py — do not edit.\n')
    put('terms.yaml', _terms_yaml())
    put('sections/CONTEXT.md', _sections_ctx())
    put('refs/CONTEXT.md', _refs_ctx(name))
    for d in ('lib', 'images', 'tables'):
        put(f'{d}/CONTEXT.md', _SUB_CTX(d))
    put('outputs/CONTEXT.md', '# Outputs\n> Research artifacts: metrics CSVs, analysis notes, generated reports, planning docs. Do not edit manually.\n\n' + ROUTE)

    verb = 'Created' if is_new else 'Adapted'
    print(f'{verb}: {root}')
    for f in created:
        print(f'  + {f}')
    for f in skipped:
        print(f'  ~ {f} (exists — skipped)')
    if is_new:
        print(f'\nNext steps:\n  cd {root}\n  git init && git remote add origin <overleaf-url>\n  git add . && git commit -m "Initial scaffold"')


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in ('new', 'adapt'):
        print('Usage:\n  paper-scaffold.py new <name>\n  paper-scaffold.py adapt <path>', file=sys.stderr)
        return 1

    if args[0] == 'new':
        dir_name = args[1].replace(' ', '_')
        root = PAPERS / dir_name
        if root.exists():
            print(f'Error: {root} already exists — use "adapt" to fill missing files.', file=sys.stderr)
            return 1
        scaffold(root, _dir_to_title(dir_name), dir_name, is_new=True)
    else:
        root = Path(args[1]).resolve()
        if not root.exists():
            print(f'Error: {root} does not exist.', file=sys.stderr)
            return 1
        scaffold(root, _dir_to_title(root.name), root.name, is_new=False)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
