# close
> What a session close writes, and what it does with each artifact afterwards.

Modules imported by [`../roundup`](../roundup): the caller keeps the sequence and the decisions, each module here keeps the work one step does.

They were `source`d shell fragments until 2026-08-29, which is why the split reads the way it does.
A fragment worked only because it shared the caller's shell state, so running it any other way did nothing and said nothing; here what a step needs arrives as arguments, and the coupling is visible in the signature. `regenerate` takes its `clean` flag from the caller for exactly that reason —
measuring it after the first write reads the close's own change as pre-existing dirt.

**One rule governs every artifact a close regenerates**: write it, then commit it by path, so another session's staged files can never ride along.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`handoff.py`](handoff.py) | [`handoff.pyi`](handoff.pyi) | `name_of`, `identity`, `records`, `started`, `transcript` | Repository handoffs: names and edit counts come from local records, never a model. |
<!-- routing:end -->
