# secret_law.py — the one definition of what counts as a secret: the patterns, the redaction a
# transcript needs, and the scan that REFUSES a file rather than cleaning it.
#
# Two families need these patterns now, so core/tools/SPECS.md § Naming puts them at this root:
# chat/ redacts a transcript it is about to write, wos/publish refuses a file it is about to copy.
#
# THE TWO JOBS ARE NOT THE SAME JOB, and the difference is the whole reason scan() exists beside
# redact(). A transcript is Lucas's own record of a conversation that already happened: the value
# has to go and the line has to stay, so it is redacted. A file crossing into a public repo has
# already failed a different test — it was never supposed to carry the value — and redacting it
# would publish the file while hiding that fact. So publish REFUSES and names the line; nobody
# silently ships a cleaned copy. A gate that fixes what it finds teaches nothing upstream.
from __future__ import annotations
import pathlib, re
from typing import NamedTuple

# core/norms/secrets.md: the versioned text carries the label, never the value.
#
# A bare 11-digit run is NOT enough to call something a CPF — a Brazilian mobile with area code is
# eleven digits too. So bare digits are redacted only near a line that says CPF; a punctuated one
# is unambiguous and goes anywhere.
FORMATTED_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
BARE_CPF = re.compile(r"\b\d{11}\b")
PASSWORD = re.compile(r"(?i)(senha\W{0,3})\d{6,}")
CPF_LABEL = "‹CPF em segredos.env›"

# How many lines a mention of "CPF" keeps colouring. In chat the number arrives a turn or two after
# the request — "Me informa o seu CPF" / "o meu é ..." — so a line-local test misses the real case.
CPF_WINDOW = 3


def redact_line(line: str, in_cpf_context: bool) -> str:
    out = PASSWORD.sub(r"\1‹em segredos.env›", FORMATTED_CPF.sub(CPF_LABEL, line))
    return BARE_CPF.sub(CPF_LABEL, out) if in_cpf_context else out


def redact(text: str) -> str:
    out, countdown = [], 0
    for line in text.split("\n"):
        if "cpf" in line.lower():
            countdown = CPF_WINDOW
        out.append(redact_line(line, countdown > 0))
        countdown -= 1
    return "\n".join(out)


# The file name the root law reserves for a secret. A tree that carries one has declared, in its own
# vocabulary, that the contents must not be published — so the NAME alone is a finding and no
# pattern has to match inside it.
SECRET_FILE = "segredos.env"

# Vendor prefixes are listed rather than generalised because each one is a claim: this exact shape
# is a live credential and nothing else wears it. A generic "long random string" rule would flag
# every git SHA and every base64 blob in the tree, and a gate that cries wolf gets switched off.
CREDENTIALS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("CPF", FORMATTED_CPF),
    ("CNPJ", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
    ("Overleaf token", re.compile(r"\bolp_[A-Za-z0-9]{20,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("OpenAI key", re.compile(r"\bsk-[A-Za-z0-9]{20,}")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("private key", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    # The shape that actually leaked here: credentials inside a git remote URL.
    ("credential in a URL", re.compile(r"https?://[^/\s:@]+:[^/\s@]{8,}@")),
    # The catch-all, deliberately last and deliberately narrow: a secret-ish NAME, an assignment,
    # and a value long enough to be one. `token: yes` and `password = ""` do not match, and that is
    # the point — the near-misses are what decide whether anyone leaves this gate on.
    ("assigned secret", re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|senha|password|secret)\b"
        r"\s*[:=]\s*[\"']?[A-Za-z0-9/+_\-]{16,}")),
)


class Finding(NamedTuple):
    """One reason a file may not be published. `evidence` names the KIND and the line, never the
    value — a report that quotes the secret copies it into wherever the report lands."""
    path: pathlib.Path
    line: int
    kind: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}  {self.kind}"


def scan_text(text: str, path: pathlib.Path) -> list[Finding]:
    found: list[Finding] = []
    countdown = 0
    for n, line in enumerate(text.split("\n"), start=1):
        for kind, pattern in CREDENTIALS:
            if pattern.search(line):
                found.append(Finding(path, n, kind))
        # Same window as the redactor, and for the same reason: eleven bare digits are a CPF only
        # where the surrounding lines say so.
        if countdown > 0 and BARE_CPF.search(line):
            found.append(Finding(path, n, "CPF"))
        countdown = CPF_WINDOW if "cpf" in line.lower() else countdown - 1
    return found


# THE FILES THIS SCANNER CANNOT SCAN: the cases that prove it. They are synthetic by rule — a test
# fixing a real leak would block the fix for it — and they are the only evidence the patterns below
# work, so a repo that refuses them is a repo that can ship this module or prove it, never both.
# NAMES, not a pattern: `test_*` would exempt every test in the workspace, which is the wide switch
# someone reaches for after one false alarm. A new case file is added here by hand, deliberately.
FIXTURES = ('test_secret_law.py', 'test_chat_stitch.py')


def scan(path: pathlib.Path) -> list[Finding]:
    """Every reason this one file may not cross. A file that cannot be read as text carries no
    finding: a binary is refused by the crossing rule, not by this one, and guessing at bytes here
    would produce findings nobody can act on."""
    if path.name in FIXTURES:
        return []
    if path.name == SECRET_FILE:
        return [Finding(path, 0, f"named {SECRET_FILE}")]
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return scan_text(text, path)


def scan_all(paths: list[pathlib.Path]) -> list[Finding]:
    """Batch-first, per core/tools/SPECS.md: no path's failure ends the run, because a caller that
    stops at the first finding makes the second one cost another whole pass."""
    return [finding for path in paths for finding in scan(path)]
