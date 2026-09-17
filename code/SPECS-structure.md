# Project structure
> How a project is laid out: its files, its module specs, and its facade.
> governs: code/<project>/
> enforced-by: core/hooks/facade/, core/tools/wos/spec-scan

## Project File Structure

Each project MUST have:
- `CONTEXT.md` — routing + architecture entry point
- `README.md` — human-facing project overview

Each project CAN have:
- `SPECS.md` — architecture decisions and design rationale (WHY, not WHAT)
- `ROADMAP.md` — pending milestones with agent-ready technical context
- `SETUP.md` — dev environment setup from scratch
- `ISSUES.md` — known-untrue state: tracked bugs with reproduction steps, plus the generated entropy and verify blocks

Skeletons for all files: [`_templates/`](_templates/)

## Module Spec Contract (Spec-Driven Development)

Rollout tracked in [`ROADMAP-spec-drive.md`](ROADMAP-spec-drive.md). Goal: the spec is the contract — a module's
verifiable inputs/outputs/invariants precede and govern its code.

A **module** = a directory under `code/<project>/` that has a `CONTEXT.md`. A module is **spec-locked**
when its `CONTEXT.md` carries a `> spec: <path>` line (mirroring the `> goal:` line convention) and the
referenced `SPEC.md` has header `status: locked`. Skeleton: [`_templates/module.SPEC.md`](_templates/module.SPEC.md).

| SPEC.md header | Meaning |
|----------------|---------|
| `status: draft` | Spec exists; read-gate NOT armed; conformance not wired |
| `status: locked` | Read-gate armed — editing this module's files requires reading its SPEC.md first (enforced by `spec-read-gate`) |
| `verify: none` | `## Examples` checked by eye only |
| `verify: make verify-fast` / `npm run verify:fast` | `## Examples` run inside the project's existing verify:fast — a broken example blocks the commit |

**Enforcement (ratchet / boy-scout, not big-bang):**
- New module dir (new `CONTEXT.md` under `code/`) → must ship a `SPEC.md` or an explicit `> spec:
  none` opt-out (`pre-commit` block).
- Editing a spec-locked module's files without reading its SPEC.md this session → hard-blocked
  (`spec-read-gate`, clone of `context-gate`).
- Editing a legacy module with no spec → non-blocking nudge only. Coverage grows as modules are touched.

Pilot: [`spacemantics/dsl/SPEC.md`](spacemantics/dsl/SPEC.md) (`status: locked`, `verify: make verify-fast`).

## Facade Pattern

Every folder with source files exposes a **facade** — the single entry point through which all
external consumers import. Nothing imports internal files from another module directly.

**Per-language convention:**

| Language | Facade file | Notes |
|----------|-------------|-------|
| TypeScript / JS | `index.ts` / `index.js` | Explicit named re-exports only — no `export *` (breaks tree-shaking) |
| Python | `__init__.py` | Explicit `__all__` required |
| Dart | `index.dart` | `export '...' show ...` pattern |
| SCSS | `_index.scss` | `@forward` only |
| Java / Kotlin | `package-info.java` / package object | Access modifiers are the facade — `public` = API, `package-private` / `internal` = hidden. No extra file needed; the compiler enforces it. |

**Rules:**
- Facade re-exports only the public API — internal helpers stay invisible
- Cross-folder imports that target a non-facade file → **hard block at commit** (`check-facade-imports.py`)
- Intra-folder imports (within the same module) always allowed
- Circular dependencies → fix the architecture, not the import rule

**Exempt from enforcement:** test files, the facade file itself, `generated/` and `vendor/` dirs.

**Reading facades:** `index.ts` / `__init__.py` / `index.dart` are read directly — `pre-read.py`
does not block them. They are already minimal interfaces. Implementation files are redirected to
their `.d.ts` / `.pyi` / `.dart.api` interface instead.

See [SETUP.md](SETUP.md) for facade templates per language.
