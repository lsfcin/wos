# Usage: core/run tools/pdf/bench/describers.py <set-dir> [--describers agy,claude,local] — describe every image in a set with each describer ALONE (no chain), then score facts hit against <set-dir>/keys.json and the OCR cross-check; one TSV row per image×describer and a total
#
# The bake-off behind core/experiments/vlm-describe.md, re-runnable against the production backends
# in core/tools/describe.py. keys.json maps an image name to {"facts": [[regex alternatives], ...]};
# a fact is hit when any alternative matches the lowercased description. The set and its keys stay
# out of git: the images come from real PDFs, and the keys name what is in them.
# `local` runs whatever WOS_LOCAL_VLM names, so another local model is one environment variable.
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE.parents[1]), str(_HERE.parents[2] / 'hooks')]
import describe  # noqa: E402


def hits(text: str, facts: list[list[str]]) -> int:
    lowered = text.lower()
    return sum(any(re.search(p, lowered) for p in alternatives) for alternatives in facts)


def run(image: Path, name: str, out: Path) -> dict:
    """One describer, one image; the text is kept so a score can be re-read without re-paying."""
    start = time.time()
    try:
        text, _by = describe.BACKENDS[name](image, describe.FIGURE_PROMPT)
    except Exception as e:  # noqa: BLE001 — a failed describer is a row, not a crash
        text = f'[ERROR] {e}'
    seconds = round(time.time() - start, 1)
    saved = out / name / f'{image.stem}.md'
    saved.parent.mkdir(parents=True, exist_ok=True)
    saved.write_text(text, encoding='utf-8', newline='\n')
    return {'text': text, 'seconds': seconds}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('set', type=Path)
    ap.add_argument('--describers', default='agy,claude,local')
    args = ap.parse_args()
    keys = json.loads((args.set / 'keys.json').read_text(encoding='utf-8'))
    totals: dict[str, list] = {}
    print('image\tdescriber\tfacts\tof\tseconds\tocr_overlap\tflagged')
    for image in sorted(args.set.glob('*.png')):
        facts = keys.get(image.name, {}).get('facts', [])
        ocr_text = describe.ocr(image)
        for name in args.describers.split(','):
            done = run(image, name, args.set / 'out')
            got, share = hits(done['text'], facts), describe.overlap(ocr_text, done['text'])
            flagged = not done['text'].strip() or (share is not None and share < describe.THRESHOLD)
            print(f"{image.name}\t{name}\t{got}\t{len(facts)}\t{done['seconds']}\t{share}\t{flagged}", flush=True)
            total = totals.setdefault(name, [0, 0, 0.0])
            total[0], total[1], total[2] = total[0] + got, total[1] + len(facts), total[2] + done['seconds']
    for name, (got, of, seconds) in totals.items():
        print(f'TOTAL\t{name}\t{got}\t{of}\t{round(seconds)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
