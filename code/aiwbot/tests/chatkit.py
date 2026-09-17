# chatkit.py — shared Telegram fakes: a chat that records every write, its bubbles, and the
# origin message replies hang off. Extracted from the Stage 3 sealing tests when Stage 4 needed
# the same three objects — the ask bubbles are sent through exactly the same reply primitives.
from __future__ import annotations


class Bubble:
    """One sent message. Records edits so "was this touched after that one was born?" is
    answerable, which is what the sealing invariant is stated in terms of."""

    def __init__(self, chat, text=""):
        self.chat = chat
        self.text = text
        self.message_id = chat.next_id()
        self.edits = 0
        self.markup = None
        self.deleted = False

    async def edit_text(self, text, parse_mode=None, reply_markup=None):
        self.text = text
        self.markup = reply_markup
        self.edits += 1
        self.chat.log.append(("edit", self.message_id))

    async def delete(self):
        self.deleted = True
        self.chat.log.append(("delete", self.message_id))

    async def edit_reply_markup(self, reply_markup=None):
        self.markup = reply_markup
        self.chat.log.append(("markup", self.message_id))


class Chat:
    def __init__(self):
        self._id = 100
        self.actions = []
        # Ordered record of every write to the chat, so "was this bubble touched AFTER a later
        # one existed?" is answerable — which is the actual sealing invariant.
        self.log = []

    def next_id(self):
        self._id += 1
        return self._id

    async def send_action(self, action):
        self.actions.append(action)


class FakeReplyAnchor:
    """The message a reply hangs off — all the router reads of it is the id."""

    def __init__(self, message_id):
        self.message_id = message_id


class FakeMsg:
    """An incoming message, seen only as "does it reply to something, and to what"."""

    def __init__(self, reply_to_message_id=None):
        self.reply_to_message = FakeReplyAnchor(reply_to_message_id) if reply_to_message_id else None


class Origin:
    """Lucas's own message: new bubbles are sent as replies to it."""

    def __init__(self):
        self.chat = Chat()
        self.sent = []

    async def reply_text(self, text, parse_mode=None, do_quote=False, reply_markup=None):
        bubble = Bubble(self.chat, text)
        bubble.markup = reply_markup
        self.sent.append(bubble)
        self.chat.log.append(("send", bubble.message_id))
        return bubble
