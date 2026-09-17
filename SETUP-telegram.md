# Setup — the chat bot
> The bot that puts this workspace in a chat: a thought captured into `brain/INBOX.md` from away
> from the PC, and a coding agent driven from the same thread. One process, one switch, one service.
> feature: bot
> enforced-by: core/tools/test/workspace/test_setup_executable.py

The five-part contract: [`SETUP.md`](SETUP.md). The bot itself is [`code/aiwbot`](code/aiwbot/CONTEXT.md)
— its shape, its provider boundary and its specs live there, and nothing about them is restated here.

**This file installs the service; it does not create the account.** A bot token comes from BotFather
and pairs with one chat, and whoever installs this has their own. Where Lucas keeps his, and the
tightness rules a credential file is written under, is `SETUP-accounts.md` § Telegram bot — private
to his clone by `core/public.txt`.

<!-- steps:start -->

## Telegram bot service
> feature: `bot` · agent: yes

The bot runs as the systemd `--user` service `aiwbot`. The unit lives **outside** the repo, at
`~/.config/systemd/user/aiwbot.service`.

It must carry `Environment=PYTHONUNBUFFERED=1`: the journal is a pipe, so Python block-buffers
stdout and every diagnostic sits in an 8 KB buffer until the process exits, which made the bot's
logs invisible exactly while it was running (2026-07-27). `Restart=always` self-heals a crash, and
the unit does not survive a reboot without a login session unless `loginctl enable-linger <user>` is
set (sudo). Switching branches or pulling takes effect only on restart.

**Precondition** `systemctl --user status aiwbot --no-pager | head -3`

**Install**
```bash
python -m pip install -r code/aiwbot/requirements.txt
systemctl --user daemon-reload
systemctl --user enable --now aiwbot
```

**Verify** — send a message from the paired chat and confirm the entry lands in `brain/INBOX.md`;
`journalctl --user -u aiwbot -n 50` if it does not.

<!-- steps:end -->
