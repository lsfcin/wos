#!/usr/bin/env python3
# What every write gate needs from its stdin: which file is being written, and how big it would get.
#
# SHARED BECAUSE THE TABLE SPLIT, NOT BECAUSE THE CODE DID. checks/pre-edit.py asked these questions
# once and refused for three reasons; gates.txt gives a row ONE feature cell, so naming either owner
# made the other's ablation row a lie (/ROADMAP.md § Measurement). The file had to become two, and
# neither half may re-derive the payload: a second copy is the drift core/hooks/ exists to catch,
# and the commit's duplication gate blocks it anyway.
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hook_input import capability, parse_stdin  # noqa: E402

# parents[3], not [2]: this file is core/hooks/checks/<name>.py, so [2] is core/ and every
# workspace-relative `vendored.txt` pattern silently fails to match — is_vendored() then always
# returns False and the size gate blocks the vendored files that list exists to waive. Latent for
# as long as pre-edit.py lived in checks/; caught by reading, not by a failure.
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


def block(*lines) -> None:
    """Reject the edit, on stderr, which is the only stream the model is handed.

    Claude Code feeds a PreToolUse exit-2's STDERR back as the blocking reason; stdout is dropped.
    The gate this came from was the only one of six printing to stdout, so every rejection arrived
    as "No stderr output" — an edit blocked with no reason attached, costing a round of
    investigation each time. It read as intermittent because it is provider-shaped, not
    path-shaped: the opencode and copilot shims concatenate both streams and were fine, and running
    the hook by hand shows stdout in the terminal. Only Claude Code went mute.
    """
    print(*lines, sep='\n', file=sys.stderr)
    sys.exit(2)


def target() -> tuple:
    """(file_path, data) for the write this call is. Exits 0 when the call is not a write.

    By capability, never by tool name (b20260901). A harness naming its tools differently still
    sends one of two payload shapes, and no reader here has ever needed the name for any reason
    but the shape.
    """
    _, tool, data, _, _ = parse_stdin()
    if capability(tool, data) != 'write':
        sys.exit(0)
    return data.get('file_path', ''), data


def written_size(file_path: str, data: dict):
    """(lines, characters) the file would hold after this write, or None when that is unknowable.

    Two payload shapes, which is the whole reason this is a function: whole `content`, or a patch.
    A patch is measured as a DELTA against what is on disk rather than by applying it — the applied
    text would have to guess which occurrence `old_string` meant, and the size law only ever needed
    the difference.
    """
    if 'content' in data:
        content = data.get('content', '')
        return len(content.splitlines()), len(content)
    if 'new_string' in data:
        if not os.path.exists(file_path):
            return None
        current = Path(file_path).read_text(encoding='utf-8', errors='replace')
        old, new = data.get('old_string', ''), data.get('new_string', '')
        return (len(current.splitlines()) + new.count('\n') - old.count('\n'),
                len(current) + len(new) - len(old))
    return None
