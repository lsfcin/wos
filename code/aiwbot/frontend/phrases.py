# phrases.py — phrase banks (natural-language variants, picked at random per message) + help text.
from __future__ import annotations
import random

# Tone (Lucas, 2026-07-26): lowercase, no trailing period. These banks arrived copied from the
# old workspace bot in sentence-case, which reads stiff in a chat bubble — an ack is an aside,
# not a sentence. Glyphs are flat for the same reason: `·` and `▸`, never the gradient emoji.
# And `·` is a DIVIDER, never an opener (Lucas, 2026-07-28): it separates (`· · ·`, `a · b`) and
# so must not lead a line — "pensando…", not "· pensando…".
# Keep all three rules when adding a bank; HELP_TEXT stays prose, since it IS a document.

CAPTURE_ACKS = [
    "guardado em brain/INBOX.md",
    "adicionado ao INBOX.md",
    "salvo em brain/INBOX.md",
    "enviado para o INBOX.md",
    "registrado em brain/INBOX.md",
]
WORKING_PHRASES = [
    "trabalhando…",
    "rodando…",
    "processando…",
    "um instante…",
    "pensando…",
]
NEW_EMPTY_PROMPT_PHRASES = [
    "sessão nova — ajusta abaixo se quiser e responde essa mensagem com o prompt",
    "beleza: configura nos botões e responde aqui com o que a sessão deve fazer",
    "sessão nova. os botões mudam harness/model/effort; responde essa mensagem com o prompt",
]
ERROR_PHRASES = [
    "deu erro: {e}",
    "algo quebrou: {e}",
    "erro ao rodar: {e}",
    "falhou: {e}",
    "rolou um erro: {e}",
]
UNKNOWN_CMD_PHRASES = [
    "não conheço {cmd}. manda /help pra ver os comandos",
    "{cmd} não existe. confere o /help",
    "comando {cmd} desconhecido — veja /help",
    "não entendi {cmd}. tenta /help",
    "{cmd}? não conheço. /help lista o que dá pra fazer",
]
SESSION_LIVE_ELSEWHERE_PHRASES = [
    "essa sessão tá aberta ao vivo em outro lugar (VSCode?) agora — fecha lá e tenta de novo",
    "não consigo continuar: essa sessão já tá em uso em outro lugar. fecha lá primeiro",
    "essa sessão parece estar aberta em outra janela — só dá pra seguir por aqui quando ela não estiver aberta em nenhum outro lugar",
]
RESUME_EMPTY_PHRASES = [
    "nenhuma sessão pra retomar ainda",
    "sem sessões no histórico — começa uma com /new",
    "ainda não tem sessão nenhuma pra retomar",
]
RESUME_ANCHOR_PHRASES = [
    "sessão retomada — responde aqui pra continuar",
    "pronto, essa é a ativa. responde essa mensagem pra seguir",
    "retomei essa sessão. manda a próxima como resposta a essa mensagem",
]
# Sent the instant a voice note lands, BEFORE the download and the ~seconds of transcription, and
# then morphed into the turn's working message (Lucas, 2026-07-28: "demora para aparecer qualquer
# feedback"). It names what is actually happening rather than saying "ok", so a slow transcription
# reads as progress instead of silence.
LISTENING_PHRASES = [
    "ouvindo o áudio…",
    "transcrevendo…",
    "escutando o recado…",
    "passando o áudio pra texto…",
]
# The provider was overloaded or the connection dropped, and the turn is being tried again by
# itself (2026-07-29). Names the reason, because a silent retry looks like a stall — and Lucas is
# usually not at the screen when it happens.
RETRY_PHRASES = [
    "a API tá sobrecarregada — tentando de novo…",
    "deu sobrecarga do lado deles. nova tentativa…",
    "falhou por sobrecarga, repetindo…",
]
TRANSCRIBE_FAIL_PHRASES = [
    "não consegui transcrever o áudio — guardei em brain/INBOX.md",
    "esse áudio não rolou de transcrever, mas já tá salvo no INBOX.md",
    "falhou a transcrição — deixei o áudio guardado no brain/INBOX.md",
]
# The agent asked something and its turn is parked on the answer (F4 Stage 4). The hint appears
# only under a question with no buttons — with buttons the affordance is on screen already. The
# toasts are what a tap says back; a stale one is the button of a question already answered.
ASK_HINT = "responde essa mensagem"
ASK_TAKEN = "anotado"
ASK_STALE = "essa pergunta já passou"

HELP_TEXT = (
    "<b>Comandos</b>\n"
    "<code>/new</code> [--backend claude|opencode] &lt;prompt&gt; — inicia sessão nova, já fica selecionada\n"
    "<code>/resume</code> [busca] — lista sessões recentes pra retomar (filtra por título se você passar um termo)\n"
    "<code>/help</code> — essa mensagem\n\n"
    "Texto, foto, áudio ou documento mandado sem <code>/</code> vai direto pro brain/INBOX.md.\n\n"
    "Responder a qualquer mensagem de sessão continua aquela sessão — não precisa digitar id.\n\n"
    "Começar com <code>bot …</code> abre sessão nova. Pode nomear harness/model logo no início "
    "(<code>bot, opencode glm resume o pdf</code> ou <code>bot sonnet explica isso</code>) — "
    "sem gastar inferência; o resto da frase é o prompt.\n\n"
    "Os botões embaixo de cada resposta mudam model e effort da sessão. "
    "O harness (claude/opencode) só dá pra escolher em sessão nova — uma sessão não troca de "
    "harness, porque nenhum dos dois importa o contexto do outro.\n\n"
    "Sessão nova herda harness/model/effort da última interação."
)


def pick(bank: list[str], **kw) -> str:
    text = random.choice(bank)
    result = text
    if kw:
        result = text.format(**kw)
    return result


def pin() -> str:
    """The still-working line held under a streaming answer — the same words a status bubble
    shows, because they are the same status."""
    return pick(WORKING_PHRASES)
