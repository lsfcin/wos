# chat_transcribe.py — batch speech-to-text over an extracted chat export; one .txt sidecar per audio.
# Resumable: an audio whose sidecar already exists is skipped, so a killed run loses nothing.
from __future__ import annotations
import sys, pathlib, subprocess, time

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / 'audio'))
import stt  # noqa: E402

# What a rejected transcript writes instead of nothing, so the stitch can say "audio, not
# understood" rather than silently dropping a turn someone actually spoke.
REJECTED = "‹áudio não transcrito — baixa confiança›"


def duration(path: pathlib.Path) -> float:
    """Seconds of audio, via ffprobe. 0.0 when the file is unreadable — it still gets tried."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, encoding='utf-8')
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def audios(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(p for p in root.rglob("*.opus"))


def sidecar(path: pathlib.Path) -> pathlib.Path:
    return path.with_suffix(".opus.txt")


def eta(done_audio: float, total_audio: float, elapsed: float) -> str:
    """Remaining wall time, extrapolated from seconds-of-audio actually processed so far —
    not from file count, because voice notes differ by an order of magnitude in length."""
    if done_audio <= 0:
        return "estimando…"
    rate = elapsed / done_audio
    left = (total_audio - done_audio) * rate
    return f"{left / 60:.0f} min restantes (·{1 / rate:.1f}x tempo real)"


def run(root: pathlib.Path, prompt: str, model=None) -> int:
    """Transcribe every audio under `root`, printing a live ETA. Returns the number written."""
    files = audios(root)
    lengths = {p: duration(p) for p in files}
    total = sum(lengths.values())
    todo = [p for p in files if not sidecar(p).exists()]
    print(f"{len(files)} áudios · {total / 60:.1f} min de áudio · {len(todo)} a fazer", flush=True)
    whisper = model if model is not None else stt.model()
    started, done_audio, written = time.time(), 0.0, 0
    for i, path in enumerate(todo, 1):
        text = stt.run(path, whisper, prompt)
        sidecar(path).write_text(text or REJECTED, encoding="utf-8", newline='\n')
        written += 1
        done_audio += lengths[path]
        elapsed = time.time() - started
        remaining = sum(lengths[p] for p in todo) - done_audio
        print(f"[{i}/{len(todo)}] {path.parent.name}/{path.name} · {elapsed / 60:.0f} min gastos · "
              f"{eta(done_audio, done_audio + remaining, elapsed)}", flush=True)
    return written
