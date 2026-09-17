# stt.py — aiwbot's binding of the shared STT: workspace vocabulary primed in (C1, C3, C4).
#
# The wrapper itself moved to core/tools/audio/stt.py — the bot is no longer the only thing here
# that listens. What stays aiwbot's is `hotwords`: priming is domain data, not wrapper logic.
# The public surface below is unchanged on purpose; SPECS.md is locked on `run(path, model)`.
from __future__ import annotations
import sys, pathlib
from . import hotwords as hotwords_data

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / 'core' / 'tools' / 'audio'))
import stt as shared  # noqa: E402

# Re-exported so `stt.confident` stays this module's API (C3 tests read it here).
confident = shared.confident


def _model():
    """Lazy-cached WhisperModel — faster_whisper is imported inside the shared boundary, so
    importing this module still succeeds with the dep uninstalled (C6)."""
    return shared.model()


def run(path: pathlib.Path, model, hotwords: str | None = None) -> str:
    """Transcribe one file with an injectable model — the C1/C3 test boundary. Failure and a
    transcript the model itself doubts both degrade to ""."""
    return shared.run(path, model, hotwords_data.as_prompt() if hotwords is None else hotwords)


def transcribe(path: pathlib.Path) -> str:
    return run(path, _model())
