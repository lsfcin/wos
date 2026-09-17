# hotwords.py — explicit editable data (C4): what the STT is primed with before it listens.
# Kept as data, not inline in stt.py, so it can be tuned without touching wrapper logic.
from __future__ import annotations

# The vocabulary the STT must not mangle. This is the CHECKLIST, not the prompt: every word here
# has to appear inside some CARRIER sentence below, which `test_as_prompt_joins_every_hotword…`
# enforces. Add a word here and the test fails until a sentence actually says it.
HOTWORDS = [
    # the models Lucas names out loud to pick one — absent until 2026-07-27, which is why
    # "claude sonnet" came back as "claudsonner" and the F3a directive silently never fired
    "claude", "sonnet", "opus", "fable", "haiku", "GLM",
    # workspace jargon
    "aiwbot", "isoroll", "spacemantics", "dobra", "cria", "instituto", "casinhas",
    "roadmap", "INBOX", "backend", "opencode", "commit", "deploy", "prompt",
    "dispatch", "harness",
    # English loanwords Portuguese speech commonly borrows verbatim
    "workspace", "feature", "branch", "merge", "pull request", "token",
    "prompt engineering", "framework", "pipeline", "webhook",
]

# Whisper imitates the *style* of what it is primed with, so a carrier written in Lucas's own
# register, correctly punctuated, is what buys punctuation back.
#
# F3b shipped this as punctuated sentences FOLLOWED BY the bare `HOTWORDS` list, on the theory
# that the two only had to share one conditioning slot. Measured against Lucas's chuveiro voice
# note on 2026-07-27, that shape scores **0.0 punctuation marks per 100 words** — the priming
# failed completely. The correction: a bare word list ANYWHERE in the prompt suppresses
# punctuation, not merely at the tail. Moving the list in front of the sentences (so the prompt
# still ENDS punctuated) scored 1.1/100 — still dead. Only dissolving the list INTO the sentences
# works, and it works decisively: **22.5/100**, on the same audio, same model.
#
#   current  "bote claudsonner me ajuda a procurar um chuveiro o meu queimou quero…"
#   this     "Bot, claude sonnet, me ajuda a procurar um chuveiro. O meu queimou. Quero…"
#
# So the rule is: the prompt is prose, end to end. Never append a word list to it — to teach the
# STT a new word, put the word in a sentence someone could actually have said.
CARRIER = [
    "Bot, roda os testes do aiwbot e me diz o que quebrou.",
    "Bot, claude sonnet, abre o roadmap do isoroll e do spacemantics.",
    "Bot, opus, faz um commit no branch do backend.",
    "Beleza, então é o seguinte: se der erro no opencode ou no claude, manda o log.",
    "Bot, fable, dá uma olhada no dobra, no cria, no instituto e nas casinhas.",
    "Usa o haiku pra isso, ou o GLM, tanto faz.",
    "Tudo bem? Ah, e não esquece do commit, do deploy e do prompt.",
    "Manda pro INBOX, abre um pull request e faz o merge da feature.",
    "O dispatch do harness tá no workspace, no pipeline, junto do webhook e do framework.",
    "Cada token conta, então prompt engineering aqui é coisa séria.",
]


def as_prompt() -> str:
    """The conditioning prompt: punctuated sentences, and nothing else. The jargon is already
    inside them — appending `HOTWORDS` here is exactly the bug fixed on 2026-07-27."""
    return " ".join(CARRIER)
