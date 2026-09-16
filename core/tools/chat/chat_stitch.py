# chat_stitch.py — a chat export becomes one readable conversation: every "audio attached" line
# gains what was actually said underneath, bot menus that repeat verbatim go, and secrets are redacted.
from __future__ import annotations
import sys, pathlib, re

# The redaction rule moved to core/tools/secret_law.py when publish/ came to need it too: a
# credential is the same credential whichever family is about to write it out.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from secret_law import redact  # noqa: E402

ATTACHED = re.compile(r"‎?([\w.\- ]+\.opus) \(arquivo anexado\)")
# A chat robot re-sends the same greeting and menu on every inbound message. Four copies of a menu
# is not conversation, and it buries the two lines a human actually typed.
BOT_NOISE = ("Agora escolha uma das opções abaixo", "*[ 1 ]* - *Orçamento*",
             "Seja bem-vindo(a) ao Cartório", "Opção inválida.",
             "Ajude-nos a melhorar a prestação de nossos serviços")


def transcript_for(audio_name: str, media: pathlib.Path) -> str | None:
    side = media / f"{audio_name}.txt"
    return side.read_text(encoding="utf-8").strip() if side.exists() else None


def fold(line: str, media: pathlib.Path) -> list[str]:
    """One export line -> the lines it becomes. An audio keeps its original line (the timestamp and
    speaker live there) and gains an indented transcript below it."""
    hit = ATTACHED.search(line)
    if not hit:
        return [line]
    said = transcript_for(hit.group(1), media)
    return [line] if said is None else [line, f"    ↳ {said}"]


def is_noise(line: str) -> bool:
    return any(marker in line for marker in BOT_NOISE)


def stitch(export: pathlib.Path, media: pathlib.Path) -> str:
    out: list[str] = []
    for line in export.read_text(encoding="utf-8").split("\n"):
        if not is_noise(line):
            out.extend(fold(line, media))
    return redact("\n".join(out))


DATE = re.compile(r"^(\d{2}/\d{2}/\d{4})")


def span(text: str) -> tuple[str, str]:
    """First and last dates in the export — the header says what period the file covers."""
    dates = [m.group(1) for m in (DATE.match(l) for l in text.split("\n")) if m]
    return (dates[0], dates[-1]) if dates else ("?", "?")


def header(who: str, text: str, audios: int) -> str:
    """The first-line description every text file in this workspace owes its routing table."""
    first, last = span(text)
    return f"# Conversa com {who} — {first} a {last}, {audios} áudios transcritos inline."


def run(export: pathlib.Path, out: pathlib.Path, who: str | None = None) -> int:
    text = stitch(export, export.parent)
    count = text.count("    ↳ ")
    name = who or out.stem
    out.write_text(f"{header(name, text, count)}\n\n{text}", encoding="utf-8", newline='\n')
    return count


if __name__ == "__main__":
    print(run(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])), "áudios costurados")
