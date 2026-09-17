# msgmap.py — bounded message_id -> value maps: which session, which scope, which panel state.
# A Telegram message is the only handle a callback carries, so everything the bot needs to know
# about a keyboard is keyed by the message it sits on — that is what keeps callback_data free.
from __future__ import annotations
from .. import config

# One answer now costs as many entries as it has bubbles (F5a/F5b anchor every chunk, not just
# the tail), so a 50-entry map would only remember a handful of turns and older answers would
# quietly stop being repliable. The map is a few hundred integers in config.json — cheap.
MAX = 400
NEW = "*new*"
DEFAULT_PANEL = "p:menu"


def _remember_by_message(map_name: str, message_id: int, value: str) -> None:
    """Oldest ids evicted first: a chat scrolls forever, the map must not."""
    cfg = config.load_config()
    mapping = cfg.get(map_name, {})
    mapping[str(message_id)] = value
    if len(mapping) > MAX:
        stale = sorted(mapping, key=int)[: len(mapping) - MAX]
        for key in stale:
            del mapping[key]
    config.save_config(**{map_name: mapping})


def _value_by_message(map_name: str, message_id: int) -> str | None:
    mapping = config.load_config().get(map_name, {})
    return mapping.get(str(message_id))


def remember_reply(message_id: int, session_id: str) -> None:
    """Anchor message -> session. Also what lets a panel tap resolve its session without
    spending any of callback_data's 64 bytes on an id (P2 D4)."""
    _remember_by_message("reply_map", message_id, session_id)


def session_for_reply(message_id: int) -> str | None:
    return _value_by_message("reply_map", message_id)


def remember_pending_new(message_id: int) -> None:
    """A bare /new sends a config bubble; the reply to THAT message is the prompt. Marking the
    message is also what routes its panel taps to the NEW scope instead of to a session."""
    _remember_by_message("pending_new", message_id, NEW)


def pending_new(message_id: int) -> str | None:
    return _value_by_message("pending_new", message_id)


def remember_ask(message_id: int, question_id: str) -> None:
    """Question bubble -> the question waiting on it, so a reply to it answers the agent instead
    of continuing the session. Kept here rather than in `ask` because eviction is the same
    problem every message map has, and it is already solved once (F4 Stage 4)."""
    _remember_by_message("ask_map", message_id, question_id)


def ask_question(message_id: int) -> str | None:
    return _value_by_message("ask_map", message_id)


def remember_panel(message_id: int, state: str) -> None:
    """Which panel state this message is showing, so a selection can return to it instead of
    collapsing to the mode row. It lives here rather than in callback_data because there is no
    room: `p:s:m:openrouter/qwen/qwen3-coder-next` already spends 40 of the 64 bytes."""
    _remember_by_message("panel_state", message_id, state)


def panel_state(message_id: int, default: str = DEFAULT_PANEL) -> str:
    """The state to redraw after applying a choice. Defaults to the dimension menu, which is
    where a tap can only have come from if the stored state was evicted."""
    found = _value_by_message("panel_state", message_id)
    return found or default


def scope_for_message(message_id: int) -> str | None:
    """Which knobs a panel tap edits: an anchored session, or NEW for a /new config bubble.
    Resolved from the message the keyboard sits on, so callback_data spends no bytes on it."""
    sid = session_for_reply(message_id)
    return sid or pending_new(message_id)
