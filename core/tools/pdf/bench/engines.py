# Usage: core/run tools/pdf/bench/engines.py <corpus-dir> [--engines docling,pymupdf] — convert every PDF in a folder with each engine through the production worker; one TSV row per PDF×engine: coverage, figures, tables, seconds, peak VRAM
#
# The bake-off behind core/experiments/pdf-engine.md, re-runnable. It measures the path the leaves
# actually take (pdf_twin.run_engine → pdf_engine.py under .venv-pdf), never a copy of the engines,
# so a number here is a number about the tool. The corpus stays out of git: real PDFs, some private.
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE.parent), str(_HERE.parents[1]), str(_HERE.parents[2] / 'hooks')]
import pdf_meta  # noqa: E402
import pdf_twin  # noqa: E402


def _vram() -> int:
    r = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                       capture_output=True, text=True, encoding='utf-8')
    return int(r.stdout.strip() or 0) if r.returncode == 0 else 0


def measure(engine: str, pdf: Path) -> dict:
    base, peak, stop = _vram(), [0], threading.Event()

    def watch() -> None:
        while not stop.is_set():
            peak[0] = max(peak[0], _vram())
            time.sleep(0.5)
    thread = threading.Thread(target=watch)
    thread.start()
    start = time.time()
    try:
        with tempfile.TemporaryDirectory(prefix='pdf-bench-') as tmp:
            result = pdf_twin.run_engine(engine, pdf, Path(tmp))
    finally:
        stop.set()
        thread.join()
    text = '\n'.join(result['pages'])
    reference = pdf_meta.reference(pdf, pdf_meta.page_texts(pdf))
    return {'coverage': pdf_meta.coverage(reference, text), 'figures': len(result['figures']),
            **pdf_meta.counts(text), 'seconds': round(time.time() - start, 1),
            'vram_mb': max(0, peak[0] - base)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('corpus', type=Path)
    ap.add_argument('--engines', default='docling,pymupdf')
    args = ap.parse_args()
    columns = ('coverage', 'figures', 'tables', 'formulas', 'seconds', 'vram_mb')
    print('\t'.join(('engine', 'pdf') + columns))
    for pdf in sorted(args.corpus.glob('*.pdf')):
        for engine in args.engines.split(','):
            try:
                row = measure(engine, pdf)
                print('\t'.join([engine, pdf.stem] + [str(row[c]) for c in columns]), flush=True)
            except Exception as e:  # noqa: BLE001 — a failed conversion is a result, not a crash
                print(f'{engine}\t{pdf.stem}\tFAILED: {e}', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
