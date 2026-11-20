# describe.py — the one image describer the tools share (pdf figures, video frames): which model looks, what the image's own text says, and whether the description can be trusted.
#
# WHY ONE MODULE. pdf and video both turn an image into text; two describers would drift into two
# prompts, two model choices and two ideas of "good enough". core/tools/SPECS.md: a module imported
# by more than one family lives at this root.
#
# THE TRUST RULE, measured 2026-09-25 (core/experiments/vlm-describe.md): every invention and every
# empty answer in the bake-off was caught by one free check — the share of the image's own OCR words
# that appear in the description. Below THRESHOLD the next describer in the chain tries; when the
# chain runs out, the best answer is kept and flagged `needs_review`. Exact text and numbers come
# from OCR or the text layer, never from the model.
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[2]
THRESHOLD = 0.5
MAX_SIDE = 1920          # larger images were cut to this in the bake-off; nothing was lost
TIMEOUT = 900            # agy took up to 394 s on one figure
MIN_WORDS = 3            # fewer OCR words than this cannot judge a description
MIN_CONFIDENCE = 60      # tesseract's per-word confidence, 0–100; below it a word is a guess
OCR_SCALES = (1, 2, 3)
# Lucas, 2026-09-25: the default is agy (cheap for him, best quality); claude is the fallback.
CHAINS = {'agy': ('agy', 'claude'), 'claude': ('claude',), 'local': ('local', 'agy', 'claude')}
DESCRIBERS = tuple(CHAINS)
# The local model is DATA: the one the bake-off kept (180/189 facts, never invented). Overridable.
LOCAL_MODEL = os.environ.get('WOS_LOCAL_VLM', 'qwen3.5:9b')
CLAUDE_LEVEL = 'medium'  # which capacity describes; core/tools/wos/levels says which model fills it

FIGURE_PROMPT = (
    "This image is a figure extracted from a PDF. Describe it so that a reader who cannot see it gets ALL of "
    "its information. Cover, in this order: (1) what kind of figure it is; (2) ALL visible text, verbatim, "
    "including titles, labels, legends, captions, axis ticks and cell values; (3) the structure: boxes, arrows "
    "and what connects to what, axes, rows and columns, panels; (4) every number or data value; (5) colours "
    "only where they carry meaning. Never guess text you cannot read: write [illegible]. Answer in the "
    "language of the text inside the image. Output only the description.")
FRAME_PROMPT = ("Describe what this image shows in two or three plain sentences. Never guess text you "
                "cannot read. Output only the description.")

WORD = re.compile(r'[a-zà-ÿ0-9]{4,}')


class Description(NamedTuple):
    text: str
    by: str | None           # which describer wrote it, e.g. `agy`, `claude:sonnet`
    overlap: float | None    # share of OCR words found in the text; None = not checkable
    needs_review: bool


def ocr(image, lang: str = 'por+eng') -> str:
    """The image's own text, verbatim — tesseract, local, zero tokens — keeping only the words
    tesseract is sure of. Small type in a figure crop comes back as junk ("tosco tomato | [tenons"),
    and junk both litters the twin and fails a correct description (2026-09-25, a 7-step diagram
    agy read perfectly scored 0.18 against it). No one scale reads every crop best — measured, a
    diagram came out at 3x and a flowchart at 2x — so each scale is tried and the fullest read wins."""
    import pytesseract
    from PIL import Image
    im = Image.open(image)
    reads = []
    for k in OCR_SCALES:
        data = pytesseract.image_to_data(im.resize((im.width * k, im.height * k), Image.LANCZOS) if k > 1
                                         else im, lang=lang, output_type=pytesseract.Output.DICT)
        lines: dict[tuple, list[str]] = {}
        for i, word in enumerate(data['text']):
            if word.strip() and float(data['conf'][i]) >= MIN_CONFIDENCE:
                lines.setdefault((data['block_num'][i], data['par_num'][i], data['line_num'][i]), []).append(word)
        reads.append([' '.join(words) for words in lines.values()])
    return '\n'.join(max(reads, key=lambda r: sum(len(line.split()) for line in r)))


def overlap(ocr_text: str, description: str) -> float | None:
    words = set(WORD.findall(ocr_text.lower()))
    if len(words) < MIN_WORDS:
        return None
    return round(sum(w in description.lower() for w in words) / len(words), 2)


def _claude_alias(level: str = CLAUDE_LEVEL) -> str:
    path = ROOT / 'core' / 'tools' / 'wos' / 'levels'
    loader = importlib.machinery.SourceFileLoader('wos_levels', str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader('wos_levels', loader))
    loader.exec_module(module)
    return module.CLAUDE[level]


def _staged(image: Path, into: Path) -> Path:
    """A copy the CLI can read from its cwd, cut to MAX_SIDE."""
    from PIL import Image
    im = Image.open(image).convert('RGB')
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    dst = into / 'image.png'
    im.save(dst)
    return dst


def _cli(cmd: list[str], image: Path, prompt: str) -> str:
    with tempfile.TemporaryDirectory(prefix='describe-') as tmp:
        staged = _staged(image, Path(tmp))
        r = subprocess.run(cmd + [f'Read the image file {staged.name} in the current directory. {prompt}'],
                           cwd=tmp, capture_output=True, text=True, encoding='utf-8', timeout=TIMEOUT,
                           stdin=subprocess.DEVNULL)
    if r.returncode:
        raise RuntimeError(r.stderr[-500:] or f'exit {r.returncode}')
    return r.stdout


_AGY_LOGGED_IN: bool | None = None


def agy_logged_in() -> bool:
    """Asked once per run, before the first figure. Logged out, `agy -p` opens a browser login on
    Lucas's screen for every figure (2026-09-26, after a forced reboot dropped the session); `agy models`
    lists nothing instead, and never prompts. Logged out, the chain goes on to claude, and says so once."""
    global _AGY_LOGGED_IN
    if _AGY_LOGGED_IN is None:
        try:
            r = subprocess.run(['agy', 'models'], capture_output=True, text=True, encoding='utf-8',
                               timeout=60, stdin=subprocess.DEVNULL)
            _AGY_LOGGED_IN = any('\t' in line for line in r.stdout.splitlines())
        except (OSError, subprocess.TimeoutExpired):
            _AGY_LOGGED_IN = False
        if not _AGY_LOGGED_IN:
            print('describe: agy is not logged in, so claude describes this run. '
                  'To bring agy back, run `agy` once in a terminal.', file=sys.stderr)
    return _AGY_LOGGED_IN


def _agy(image: Path, prompt: str) -> tuple[str, str]:
    return _cli(['agy', '--disable-slash-commands', '--dangerously-skip-permissions', '-p'],
                image, prompt), 'agy'


def _claude(image: Path, prompt: str) -> tuple[str, str]:
    alias = _claude_alias()
    return _cli(['claude', '--model', alias, '--allowedTools', 'Read', '-p'], image, prompt), f'claude:{alias}'


def _local(image: Path, prompt: str) -> tuple[str, str]:
    import base64
    import json
    import urllib.request
    with tempfile.TemporaryDirectory(prefix='describe-') as tmp:
        data = base64.b64encode(_staged(image, Path(tmp)).read_bytes()).decode()
    body = json.dumps({'model': LOCAL_MODEL, 'prompt': prompt, 'stream': False, 'think': False, 'images': [data],
                       'options': {'num_ctx': 8192, 'temperature': 0, 'num_predict': 2048,
                                   'repeat_penalty': 1.15}}).encode()
    req = urllib.request.Request('http://localhost:11434/api/generate', body,
                                 {'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=TIMEOUT))['response'], f'local:{LOCAL_MODEL}'


BACKENDS = {'agy': _agy, 'claude': _claude, 'local': _local}


def describe(image, describer: str = 'agy', ocr_text: str = '', prompt: str = FIGURE_PROMPT,
             backends: dict | None = None) -> Description:
    """Walk the describer's chain until one answer passes the OCR cross-check.

    A failed or empty answer is skipped, never raised: one figure must not end a batch. When no
    answer passes, the one with the best overlap is kept and flagged.
    """
    backends = backends or BACKENDS
    kept = None
    for name in CHAINS[describer]:
        if name in ('agy', 'claude') and backends is BACKENDS and not shutil.which(name):
            continue
        if name == 'agy' and backends is BACKENDS and not agy_logged_in():
            continue
        try:
            text, by = backends[name](Path(image), prompt)
        except Exception:  # noqa: BLE001 — a failed describer is a reason to try the next one
            continue
        text = text.strip()
        if not text:
            continue
        share = overlap(ocr_text, text)
        if share is None or share >= THRESHOLD:
            return Description(text, by, share, False)
        if kept is None or share > (kept.overlap or 0):
            kept = Description(text, by, share, True)
    return kept or Description('', None, None, True)
