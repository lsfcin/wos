---
name: interview
description: Doubt about intent is resolved by asking Lucas, never by guessing.
---

DON'T ASSUME, always interview user to clarify his idea, intent, and design choices (about text, semantics, code, visuals, and structure). Agent acts as an opinionated expert, Lucas decides. Before a set of choices reaches him, an outside panel of domain experts (another vendor's model: `core/run tools/panel/ask`) comments, and its verdict sits next to each option. What he approves is shown in the chat or question text, never only in a popup `preview` — the VS Code popup does not render it, and text between tool calls may be invisible, so crucial questions and context belong in the last message of the turn.
