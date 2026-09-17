# bot.py — PTB wiring: allowlist, /new + reply-to-continue dispatch, plain text/media -> INBOX.
from __future__ import annotations
import asyncio
from telegram import BotCommand, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from .interview import ask, askserver
from .select import choices, panel, panelmenu
from . import config, inbox, phrases, reply
from .text import format
from .session import msgmap, registry, resume
from .turn import startword, helpers, runner
from .voice import stt

WORKSPACE_DIR = config.WORKSPACE_DIR


_strip_bot_prefix = startword.strip_prefix


def _empty_guard(transcript: str) -> bool:
    """C3: an empty/whitespace-only transcript must not be dispatched."""
    return not transcript.strip()


async def _cmd_new(msg, arg: str) -> None:
    """Tapping /new in Telegram's command menu sends it bare, so an empty prompt answers with a
    config bubble instead of an error: adjust harness/model/effort on it, then reply with the
    prompt. Telegram allows exactly one reply_markup per message, so this bubble carries the
    keyboard and gives up ForceReply's auto-focus — Lucas's call, 2026-07-23."""
    backend_name, prompt = helpers.parse_new_arg(arg)
    if backend_name:
        registry.set_setting(registry.NEW, "backend", backend_name)
    if not prompt.strip():
        invite = format.plain(phrases.pick(phrases.NEW_EMPTY_PROMPT_PHRASES))
        markup = panelmenu.root_markup(registry.NEW)
        asked = await reply.safe_reply(msg, invite, reply_markup=markup)
        if asked is not None:
            msgmap.remember_pending_new(asked.message_id)
        return
    await runner.start_new(msg, prompt)


async def _route_text(msg, text: str, context, *, spoken: bool = False, working=None) -> None:
    """Shared reply-continue / pending-new / "bot"-prefix / INBOX-fallback routing (steps
    3-6 of the old `_handle_message`), reused verbatim by text (spoken=False) and voice
    (spoken=True, C2/C5)."""
    if msg.reply_to_message is not None:
        replied_to = msg.reply_to_message.message_id
        # A reply to a question the agent is still waiting on answers THAT, before anything else:
        # the turn is blocked inside the daemon, so this text belongs to the running turn rather
        # than starting a new exchange with it (F4 Stage 4).
        question = ask.question_of(replied_to)
        if question and ask.answer(question, text):
            return
        sid = msgmap.session_for_reply(replied_to)
        if sid:
            await runner.handle_reply_continue(msg, sid, text, spoken=spoken, working=working)
            return
        awaiting = msgmap.pending_new(replied_to)
        if awaiting:
            await runner.start_new(msg, text, spoken=spoken, working=working)
            return
    bot_prompt = _strip_bot_prefix(text)
    if bot_prompt is not None:
        prompt = helpers.apply_directives(bot_prompt)
        await runner.start_new(msg, prompt, spoken=spoken, working=working)
        return
    inbox.append_entry(inbox.build_entry(text, None, forwarded=msg.forward_origin is not None))
    await reply.safe_reply(msg, format.plain(phrases.pick(phrases.CAPTURE_ACKS)))


async def _handle_voice(msg, context) -> None:
    """C1/C3: transcribe, then either route through the same text dispatch (spoken=True) or
    degrade safely to the untranscribed-INBOX fallback."""
    # Before the download and the seconds of transcription, not after: an audio turn used to sit
    # silent until whisper finished, which reads as "the bot ignored me" (Lucas, 2026-07-28).
    heard_msg = await reply.safe_reply(msg, format.plain(phrases.pick(phrases.LISTENING_PHRASES)))
    path = await inbox.save_media(msg.voice.file_id, context, ".ogg")
    transcript = stt.transcribe(path)
    if _empty_guard(transcript):
        inbox.append_entry(inbox.build_entry("voice note (untranscribed)", path, forwarded=msg.forward_origin is not None))
        await reply.safe_reply(msg, format.plain(phrases.pick(phrases.TRANSCRIBE_FAIL_PHRASES)))
        return
    # The echo is no longer a message of its own: `run_and_deliver` quotes this same string at
    # the top of every answer bubble (Lucas, 2026-07-28). What is echoed is still the NORMALIZED
    # transcript, so it shows what actually reached the session, cleanup included.
    heard = startword.normalize(transcript)
    await _route_text(msg, heard, context, spoken=True, working=heard_msg)


async def _dispatch_command(text: str, msg) -> None:
    parts = text.split(maxsplit=1)
    cmd, arg = parts[0], (parts[1].strip() if len(parts) > 1 else "")
    if cmd == "/help":
        await reply.safe_reply(msg, phrases.HELP_TEXT)
    elif cmd == "/new":
        await _cmd_new(msg, arg)
    elif cmd == "/resume":
        await resume.cmd_resume(msg, arg, WORKSPACE_DIR)
    else:
        await reply.safe_reply(msg, format.plain(phrases.pick(phrases.UNKNOWN_CMD_PHRASES, cmd=cmd)))


def _log_entities(msg) -> None:
    """What formatting Telegram actually delivers to a bot. Bot API 10.0's entity list has no
    HEADING and no TABLE, which says the new rich editor is a client-side composer rather than
    new bot surface — but that is an argument from a constants list, and Lucas's screenshots
    show the composer really does offer both. So the question is settled by measurement: send
    the bot a message written with headings and a table and read this line (2026-07-27)."""
    found = list(msg.entities or []) + list(msg.caption_entities or [])
    if found:
        kinds = sorted({e.type for e in found})
        print(f"entities: {kinds}")


async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.chat_id != config.allowed_chat_id():
        return
    msg = update.message
    _log_entities(msg)
    if msg.text and msg.text.startswith("/"):
        context.application.create_task(runner.guarded(_dispatch_command(msg.text, msg), msg))
        return
    if msg.text:
        context.application.create_task(runner.guarded(_route_text(msg, msg.text, context, spoken=False), msg))
        return
    if msg.voice is not None:
        context.application.create_task(runner.guarded(_handle_voice(msg, context), msg))
        return
    forwarded = msg.forward_origin is not None
    if msg.photo:
        path = await inbox.save_media(msg.photo[-1].file_id, context, ".jpg")
        inbox.append_entry(inbox.build_entry(msg.caption or "(photo)", path, forwarded=forwarded))
    elif msg.document is not None:
        suffix = "." + (msg.document.file_name or "file").rsplit(".", 1)[-1]
        path = await inbox.save_media(msg.document.file_id, context, suffix)
        inbox.append_entry(inbox.build_entry(msg.caption or "(document)", path, forwarded=forwarded))
    else:
        return
    await reply.safe_reply(msg, format.plain(phrases.pick(phrases.CAPTURE_ACKS)))


async def _post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("new", "Inicia sessão nova com um prompt"),
        BotCommand("resume", "Retoma uma sessão recente"),
        BotCommand("help", "Lista os comandos"),
    ])
    # Off the event loop (it shells a CLI), and awaited before polling starts so no tap can
    # race the warm and pay for it (F3c).
    await asyncio.to_thread(choices.warm)
    # The MCP endpoint each turn's CLI is pointed at, in this same loop so its handler can reach
    # the chat. A port it cannot bind leaves ask disabled and the daemon otherwise intact.
    listening = await askserver.start()
    print(f"aiwbot: ask server on {askserver.HOST}:{listening}" if listening else "aiwbot: no ask server")


def main() -> None:
    # The `bot` switch at the one moment that stops everything: the process refuses to start.
    # Imported HERE and not at the top because the sys.path hop to core/tools is inbox's, and it
    # has run by the time this is called — the other half of the same switch lives there.
    import tool_law
    tool_law.require('bot')
    app = Application.builder().token(config.bot_token()).post_init(_post_init).build()
    app.add_handler(CallbackQueryHandler(ask.handle_callback, pattern="^a:"))
    app.add_handler(CallbackQueryHandler(panel.handle_callback, pattern="^p:"))
    app.add_handler(CallbackQueryHandler(resume.handle_callback, pattern="^(resume|page|noop):"))
    app.add_handler(MessageHandler(filters.ALL, _handle_message))
    print("aiwbot: polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
