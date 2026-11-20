# pdf_cli.py — the command line both engine leaves share: many PDFs per call, one line each, a summary naming the failures, and the review pass.
#
# Batch-first (core/tools/SPECS.md § A step an agent must never skip has to cost one call): a folder
# of 97 PDFs is one invocation, and one PDF's failure never ends the run.
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import describe
import pdf_meta
import pdf_twin

REVIEW_DPI = 100
FLAGGED_PAGE = re.compile(r'<!-- page (\d+) -->(.*?)(?=<!-- page \d+ -->|\Z)', re.S)


def parse(argv: list[str], leaf: str) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog=f'core/run tools/pdf/{leaf}')
    ap.add_argument('pdfs', nargs='*', type=Path)
    ap.add_argument('--from', dest='listing', type=Path, help='a file with one PDF path per line')
    ap.add_argument('--describer', choices=describe.DESCRIBERS, default='agy')
    ap.add_argument('--origin', help='live URL or Drive id of the PDF (one PDF only)')
    ap.add_argument('--description', help="what the PDF is, for the routing table (one PDF only)")
    ap.add_argument('--force', action='store_true', help='rebuild even when the twin is fresh')
    ap.add_argument('--review', action='store_true', help='render the flagged pages for an agent to compare')
    ap.add_argument('--reviewed-by', metavar='WHO', help='stamp the twin reviewed after fixing it')
    args = ap.parse_args(argv)
    if args.listing:
        args.pdfs += [Path(ln.strip()) for ln in args.listing.read_text(encoding='utf-8').splitlines()
                      if ln.strip()]
    if not args.pdfs:
        ap.error('no PDF given')
    if args.origin and len(args.pdfs) != 1:
        ap.error('--origin names the source of ONE PDF')
    if args.description and len(args.pdfs) != 1:
        ap.error('--description describes ONE PDF')
    return args


def label(pdf: Path, text: str) -> str:
    """Set the twin's description, the line its parent CONTEXT.md routes it by."""
    twin = pdf_meta.twin_of(pdf)
    pdf_meta.replace_frontmatter(twin, description=text)
    return f'labelled  {twin}'


def flagged_pages(twin: Path) -> list[int]:
    """Pages a person should look at: the ones holding a flagged figure, or all when coverage is low."""
    front = pdf_meta.read_frontmatter(twin)
    text = twin.read_text(encoding='utf-8')
    if (front.get('audit') or {}).get('word_coverage', 1) < pdf_twin.REVIEW_COVERAGE:
        return [int(n) for n, _ in FLAGGED_PAGE.findall(text)]
    return [int(n) for n, body in FLAGGED_PAGE.findall(text) if 'needs_review: true' in body]


def review(pdf: Path, leaf: str) -> str:
    twin = pdf_meta.twin_of(pdf)
    if not pdf_meta.read_frontmatter(twin).get('needs_review'):
        return f'nothing flagged  {twin}'
    out = twin.parent / 'review'
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    pages = flagged_pages(twin) or [1]
    pdf_meta.render(pdf, out / 'page', pages, REVIEW_DPI)
    return (f'review  {twin}\n  pages {pages} rendered in {out}/ — read each image, compare it with its\n'
            f'  `<!-- page N -->` section, fix the .md, then run:\n'
            f'  core/run tools/pdf/{leaf} {pdf} --reviewed-by <you>')


def stamp(pdf: Path, who: str) -> str:
    twin = pdf_meta.twin_of(pdf)
    pdf_meta.replace_frontmatter(twin, reviewed_by=who, needs_review=False)
    shutil.rmtree(twin.parent / 'review', ignore_errors=True)
    return f'reviewed  {twin}  by {who}'


def convert(pdf: Path, engine: str, args: argparse.Namespace) -> str:
    done = pdf_twin.build(pdf, engine, args.describer, args.origin, args.force)
    line = f"{done['status']:8s} {done['twin']}"
    if done.get('audit'):
        line += '  ' + ' '.join(f'{k}={v}' for k, v in done['audit'].items())
    if done.get('needs_review'):
        line += '  NEEDS REVIEW'
    if done.get('secrets'):
        line += f"  SECRET ({', '.join(done['secrets'])}) — the twin is gitignored whole"
    return line


def main(engine: str, leaf: str, argv: list[str]) -> int:
    args = parse(argv, leaf)
    failed = []
    for pdf in args.pdfs:
        try:
            if not pdf.is_file():
                raise FileNotFoundError(f'no such PDF: {pdf}')
            if args.reviewed_by:
                print(stamp(pdf, args.reviewed_by), flush=True)
            elif args.review:
                print(review(pdf, leaf), flush=True)
            else:
                print(convert(pdf, engine, args), flush=True)
            if args.description:
                print(label(pdf, args.description), flush=True)
        except pdf_twin.EngineMissing as e:
            print(e, file=sys.stderr)
            return 2
        except Exception as e:  # noqa: BLE001 — one PDF's failure never ends the batch
            failed.append(pdf)
            print(f'FAILED   {pdf}: {e}', flush=True)
    print(f'\n{len(args.pdfs) - len(failed)}/{len(args.pdfs)} done' +
          (f'; failed: {", ".join(map(str, failed))}' if failed else ''))
    return 1 if failed else 0
