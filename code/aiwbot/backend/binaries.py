# binaries.py — resolve a CLI's executable: PATH first, then the places its installer puts it.
from __future__ import annotations
import glob
import pathlib
import shutil

# The bot runs under systemd --user, whose PATH is the login default — it does NOT carry the
# per-tool bin directories a shell rc adds. `opencode` lives in ~/.opencode/bin and was simply
# invisible to the service, which silently emptied the model catalogue and would have failed any
# opencode turn outright. Every backend resolves its binary through here for that reason.
_HOMES = {
    "claude": (".vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude",),
    "opencode": (".opencode/bin/opencode", ".local/bin/opencode"),
}


def _from_home(patterns: tuple[str, ...]) -> str | None:
    home = pathlib.Path.home()
    found = None
    for pattern in patterns:
        matches = glob.glob(str(home / pattern))
        if matches:
            ordered = sorted(matches)
            found = ordered[-1]
            break
    return found


def resolve(name: str) -> str:
    """Absolute path to the CLI, or raise. PATH wins so a shell override still applies."""
    on_path = shutil.which(name)
    result = on_path
    if not result:
        patterns = _HOMES.get(name, ())
        result = _from_home(patterns)
    if not result:
        raise RuntimeError(f"{name} binary not found (PATH + known install dirs)")
    return result


def find(name: str) -> str | None:
    """Same resolution, but None instead of raising — for callers that degrade (the catalogue)."""
    found = None
    try:
        found = resolve(name)
    except RuntimeError:
        found = None
    return found
