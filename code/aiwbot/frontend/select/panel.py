# panel.py — panel routing: which grid a tap opens, and which scope it writes to.
from __future__ import annotations
import asyncio
from . import choices, labels, panelmenu
from .. import config
from ..session import msgmap, registry

_STALE = "Essa mensagem é antiga demais — retoma a sessão com /resume."
# One message per dimension. A single generic "sem controle de esforço" for any empty list is
# what made an unreachable opencode binary surface as an effort complaint on the model button.
_EMPTY = {"h": "Nenhum harness disponível.",
          "m": "Não consegui listar os modelos desse harness.",
          "e": "Esse modelo não expõe controle de esforço."}
# Harness stores as `backend` because that is the key the session registry has always used for
# "who owns this lineage"; the word on screen is harness (choices.LABELS).
_KEY = {"h": "backend", "m": "model", "e": "effort"}


async def _redraw(query, note: str | None, markup, state: str | None = None) -> None:
    """Every render records which state the message now shows, so a later selection knows where
    to return to (Lucas, 2026-07-23: a choice should step back one level, like `‹`).

    The two Telegram calls a tap needs are independent — `answerCallbackQuery` clears the
    button's spinner, `editMessageReplyMarkup` moves the bracket — so they go out together.
    Sequential they cost two round trips; concurrent, one. Measured from this machine: 222 ms
    median per call, so ~445 ms → ~222 ms. That one round trip is the floor — a Telegram client
    renders an inline keyboard only from server state, there is no local echo to beat it (F3c)."""
    if state is not None:
        mid = query.message.message_id
        msgmap.remember_panel(mid, state)
    answering = query.answer(text=note)
    editing = query.edit_message_reply_markup(reply_markup=markup)
    await asyncio.gather(answering, editing)


async def _to_root(query, scope: str, note: str | None = None) -> None:
    markup = panelmenu.root_markup(scope)
    await _redraw(query, note, markup, "p:root")


def _values_of(scope: str, dim: str) -> tuple[list[str], list]:
    """(values, extra buttons). Only the model picker carries an `all` escape into the provider
    drill-down, and only when the catalogue is bigger than the shortlist."""
    values, deep = choices.values_for(scope, dim)
    extra: list = []
    if deep:
        button = panelmenu.all_button()
        extra = [button]
    return values, extra


async def _dimension(query, scope: str, dim: str, expanded: bool, page: int,
                     note: str | None = None) -> None:
    values, extra = _values_of(scope, dim)
    if not values:
        await query.answer(text=_EMPTY[dim], show_alert=True)
    else:
        key = _KEY[dim]
        current = registry.setting_for(scope, key)
        markup = panelmenu.values_markup(dim, values, current, expanded=expanded,
                                         page=page, extra=extra)
        state = f"p:x:{dim}:{page}" if expanded else f"p:d:{dim}"
        await _redraw(query, note, markup, state)


def _drop_stale_effort(scope: str) -> None:
    """Changing model or harness can invalidate the effort: the vocabularies differ per model,
    so an effort the new one never declared would build an argv its CLI rejects."""
    current = registry.setting_for(scope, "effort")
    if current:
        values = choices.effort_values(scope)
        if current not in values:
            registry.set_setting(scope, "effort", None)


def apply(scope: str, dim: str, value: str) -> str:
    """Persist one choice and return the toast that explains it. Harness only ever reaches here
    in the NEW scope — a live session's menu does not offer it (SPECS AD-11)."""
    key = _KEY[dim]
    registry.set_setting(scope, key, value)
    if dim == "h":
        registry.set_setting(scope, "model", None)
    if dim in ("h", "m"):
        _drop_stale_effort(scope)
    shown = labels.model_label(value) if dim == "m" else value
    return f"{choices.LABELS[dim]}: {shown}"


async def _choose(query, scope: str, dim: str, value: str) -> None:
    """Apply, then redraw the state the tap came from — you see the bracket move without losing
    your place in the list. Only a harness change forces a step back, because it invalidates the
    model and effort the deeper states were showing.

    The toast rides along to the redraw's single `answerCallbackQuery`; answering here as well
    made the most common tap of all cost three sequential round trips instead of one (F3c)."""
    note = apply(scope, dim, value)
    mid = query.message.message_id
    state = "p:menu" if dim == "h" else msgmap.panel_state(mid)
    parts = state.split(":", 3)
    await _route(query, scope, parts, note)


async def _route(query, scope: str, parts: list[str], note: str | None = None) -> None:
    """Every branch ends in exactly ONE `_redraw`, which is what holds a tap to one round trip:
    a note produced by a choice rides in that call's answer rather than in a second one."""
    head = parts[1]
    if head == "menu":
        markup = panelmenu.menu_markup(scope)
        await _redraw(query, note, markup, "p:menu")
    elif head == "root":
        await _to_root(query, scope, note)
    elif head == "mode":
        # Keyboards already in the chat still carry BUILD/PLAN buttons; the mode they name no
        # longer exists (2026-07-28), so the tap redraws the current panel instead of setting it.
        await _to_root(query, scope, note)
    elif head == "d":
        await _dimension(query, scope, parts[2], False, 0, note)
    elif head == "x":
        page = int(parts[3])
        await _dimension(query, scope, parts[2], True, page, note)
    elif head == "s":
        await _choose(query, scope, parts[2], parts[3])
    elif head == "g":
        markup = panelmenu.providers_markup(scope)
        await _redraw(query, note, markup, "p:g")
    elif head == "p":
        page = int(parts[3])
        markup = panelmenu.provider_markup(scope, parts[2], page)
        await _redraw(query, note, markup, f"p:p:{parts[2]}:{page}")


async def handle_callback(update, context) -> None:
    """Panel taps carry no scope: the keyboard always sits on a message the bot remembers — an
    anchored session or a /new config bubble — so `scope_for_message` resolves it and the whole
    64-byte callback_data budget stays free for values (P2 D4)."""
    query = update.callback_query
    if query is None or query.message is None:
        return
    if query.message.chat_id != config.allowed_chat_id():
        return
    scope = msgmap.scope_for_message(query.message.message_id)
    if scope is None:
        await query.answer(text=_STALE, show_alert=True)
        return
    data = query.data or ""
    parts = data.split(":", 3)
    await _route(query, scope, parts)
