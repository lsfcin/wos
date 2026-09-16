# gates — Specs
> Why each hook test exists, and the one structural exception to running the real hook.

Companion to [`CONTEXT.md`](CONTEXT.md), which routes into this directory. Split out 2026-08-15 when
the head crossed `CONTEXT_HEAD_WARN`: rationale is a contract, and `CONTEXT.md` is the only
enforced-read type, so it is charged to every session in the folder (`core/SCHEMA.md` § Placement).

## Why stderr is the whole subject of `test_b4_gate_messages.py`

A `PreToolUse` exit-2's stderr is fed back to the model and its stdout is dropped, so a gate printing
to stdout blocks with no reason attached and reads as "No stderr output". That was B4, and this file
carries the id because the FIXED gate matches a bug to a spec by **filename** — the proof already
existed under a name that did not name it, which is a fix nobody could close.

## Why `test_subagent_gate.py` exists

The subagent exemption was real before it was decided — a worker inherited the parent's `session_id`
and therefore its seen-set, leaving it ungated only for folders the parent happened to visit. Ruled
deliberate 2026-08-15; measured in
[`core/experiments/subagent-context-chain.md`](../../../../experiments/subagent-context-chain.md).

## Why `test_bash_compact_rewrite.py` sits beside gates it does not resemble

It covers a `PreToolUse` hook that never blocks, and its failure mode is the mirror of a gate's: a
gate that wrongly fires costs a retry, a rewriter that wrongly fires runs a command nobody wrote.
The contract it holds is [`core/hooks/compact/SPECS.md`](../../../../hooks/compact/SPECS.md), which
is why its risk cases outnumber its success cases.

## The one structural exception

All three run the real hook as a subprocess against a synthetic payload, so they assert the wiring
rather than the source text. `test_the_spec_gate_is_not_exempted` is the deliberate exception: it
reads `spec-read-gate.py` for the *absence* of the exemption helper, because proving a gate does
**not** opt out is easier structurally than constructing a spec-locked module in a tmp tree.
