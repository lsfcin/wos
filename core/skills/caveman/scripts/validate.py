# Post-compression checks: what the model was forbidden to touch must be identical.
"""
Errors block the write and trigger a targeted fix pass; warnings are recorded and
tolerated. The split matters: losing a URL or a code block is data loss, whereas a
reordered heading or a merged bullet is the compression doing its job.

Extractors live in extract.py. CLI: python3 -m scripts.validate <original> <compressed>
"""

from collections import Counter
from pathlib import Path

from .extract import (
    count_bullets, extract_code_blocks, extract_headings,
    extract_inline_codes, extract_paths, extract_urls, read_file,
)


class ValidationResult:
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []

    def add_error(self, msg):
        self.is_valid = False
        self.errors.append(msg)

    def add_warning(self, msg):
        self.warnings.append(msg)


def validate_headings(orig, comp, result):
    h1 = extract_headings(orig)
    h2 = extract_headings(comp)
    if len(h1) != len(h2):
        result.add_error(f"Heading count mismatch: {len(h1)} vs {len(h2)}")
    if h1 != h2:
        result.add_warning("Heading text/order changed")


def validate_code_blocks(orig, comp, result):
    if extract_code_blocks(orig) != extract_code_blocks(comp):
        result.add_error("Code blocks not preserved exactly")


def validate_urls(orig, comp, result):
    u1 = extract_urls(orig)
    u2 = extract_urls(comp)
    if u1 != u2:
        result.add_error(f"URL mismatch: lost={u1 - u2}, added={u2 - u1}")


def validate_paths(orig, comp, result):
    p1 = extract_paths(orig)
    p2 = extract_paths(comp)
    if p1 != p2:
        result.add_warning(f"Path mismatch: lost={p1 - p2}, added={p2 - p1}")


def validate_bullets(orig, comp, result):
    b1 = count_bullets(orig)
    b2 = count_bullets(comp)
    if b1 == 0:
        return
    if abs(b1 - b2) / b1 > 0.15:
        result.add_warning(f"Bullet count changed too much: {b1} -> {b2}")


def validate_inline_codes(orig, comp, result):
    c1 = Counter(extract_inline_codes(orig))
    c2 = Counter(extract_inline_codes(comp))
    if c1 == c2:
        return
    lost = set(c1.keys()) - set(c2.keys())
    added = set(c2.keys()) - set(c1.keys())
    # A code span kept but repeated fewer times is still a loss.
    for code, count in c1.items():
        if code in c2 and c2[code] < count:
            lost.add(f"{code} (lost {count - c2[code]} of {count} occurrences)")
    if lost:
        result.add_error(f"Inline code lost: {lost}")
    if added:
        result.add_warning(f"Inline code added: {added}")


CHECKS = (
    validate_headings, validate_code_blocks, validate_urls,
    validate_paths, validate_bullets, validate_inline_codes,
)


def validate(original_path: Path, compressed_path: Path) -> ValidationResult:
    result = ValidationResult()
    orig = read_file(original_path)
    comp = read_file(compressed_path)
    for check in CHECKS:
        check(orig, comp, result)
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python3 -m scripts.validate <original> <compressed>")
        sys.exit(1)

    res = validate(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
    print(f"\nValid: {res.is_valid}")
    if res.errors:
        print("\nErrors:")
        for e in res.errors:
            print(f"  - {e}")
    if res.warnings:
        print("\nWarnings:")
        for w in res.warnings:
            print(f"  - {w}")
