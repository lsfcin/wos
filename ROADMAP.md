# Roadmap
> What this repo intends to become. A finished item is deleted; git is the history.

**This repo is synced, not authored.** Everything under `core/` arrives from the workspace that
publishes it, one way — so a change to a rule, a hook or a tool is proposed upstream, and a plan for
one does not live here. This file holds what is about the PUBLISHED repo itself.

## Open

**the ablation this repo exists to make possible**
*What* — variants of this checkout, one feature switched off in each, against one task suite.
*Why* — the workspace compensates for model failures, and a rule that outlives its failure is pure
cost. Every switch is already declared in [`core/features.txt`](core/features.txt); nothing here has
ever been measured against its own absence.
*Done when* — a per-feature verdict is readable.

**the clone a student runs without being told anything**
*What* — [`SETUP.md`](SETUP.md) run end to end by someone who has not seen the workspace it came
from, and what they got stuck on written down.
*Why* — the install contract is the whole product here, and it has only ever been run by the machine
that wrote it.
*Done when* — someone outside clones it, follows the file, and `./verify.py fast` is green.
