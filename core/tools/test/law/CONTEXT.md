# law
> Level 0: what a file is, what a name may be, and how big a session may get.

What stays here is the law **itself** — the definitions every other check reads through, and the
gate that admits a filename. The checks that consume it moved into
[`entropy/`](entropy/CONTEXT.md) on 2026-08-15, so this directory answers *what is legal* and that
one answers *what the tree actually contains*.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`entropy/`](entropy/CONTEXT.md) | What each entropy check counts, and where it must stay silent. **One file per check, not one per module** — so a name here answers to a question, and only sometimes to a file next door. |
| [`platform/`](platform/CONTEXT.md) | The platform boundary's coverage: the one module allowed to know what an operating system is, and the credential-tightness ruling that rides on it. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_b20260902_a_section_citation_survives_the_section_moving_away.py`](test_b20260902_a_section_citation_survives_the_section_moving_away.py) | [`test_b20260902_a_section_citation_survives_the_section_moving_away.pyi`](test_b20260902_a_section_citation_survives_the_section_moving_away.pyi) | `section_hits` | T0 a `<file>.md § <Section>` citation names a section that is really there. |
| [`test_char_cap.py`](test_char_cap.py) | [`test_char_cap.pyi`](test_char_cap.pyi) | — | T0 document cap: how big one authored file may be in characters, at the two declared levels. Zero-token, runs in verify-fast. |
| [`test_citation_gate.py`](test_citation_gate.py) | [`test_citation_gate.pyi`](test_citation_gate.pyi) | — | T0 roadmap item numbers may not be cited outside a roadmap. Zero-token, runs in verify-fast. |
| [`test_context_meter.py`](test_context_meter.py) | [`test_context_meter.pyi`](test_context_meter.pyi) | — | T0 context meter (core/SPECS.md § AD-09): the session-size signal that decides when to hand off. Zero-token, runs in verify-fast. |
| [`test_description_gate.py`](test_description_gate.py) | [`test_description_gate.pyi`](test_description_gate.pyi) | — | T0 description check: a file this commit adds must be able to describe itself. Zero-token, verify-fast. |
| [`test_file_law.py`](test_file_law.py) | [`test_file_law.pyi`](test_file_law.pyi) | — | T0 file law (core/hooks/SPECS.md). Zero-token, runs in verify-fast. |
| [`test_type_gate.py`](test_type_gate.py) | [`test_type_gate.pyi`](test_type_gate.pyi) | — | T0 type gate (Level 0, law in core/SCHEMA.md): the uppercase allowlist. Zero-token, runs in verify-fast. |
<!-- routing:end -->
