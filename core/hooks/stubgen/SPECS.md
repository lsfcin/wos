# stubgen — Specs
> Which interface each language gets, what generates it, and the one supported way to lift the size
> cap while you work.

Companion to [`CONTEXT.md`](CONTEXT.md), which routes into this directory. Moved out of [`../SPECS.md`](../SPECS.md) on 2026-09-05: the enforcement layer's spec had grown to 376 lines against a 200 cap, and a rule about what a generator writes belongs beside the generator rather than in the root's law.

## Interface files

Every save of a supported source file produces its interface unconditionally — universal, no per-project config. `stubs.py` holds the single copy of every generator invocation; `post-edit.sh` calls it on save and the pre-commit `interfaces` stage calls it again on what is staged.

| Language | Output | Tool | Notes |
|----------|--------|------|-------|
| Python | `.pyi` | `stubgen` | on every edit and every commit |
| JavaScript | `.d.ts` | `tsc --allowJs --emitDeclarationOnly` | `jsconfig.json` created automatically if missing (IDE use only) |
| TypeScript | `.d.ts` | `tsc --emitDeclarationOnly` | `tsconfig.json` created automatically if no ancestor config is found |
| Dart | `.dart.api` | `dart-api-extract.py` | public class/mixin/method signatures; needs Python 3 only, no Dart SDK |
| LaTeX | `.texif` | `tex-interface-gen.py` | structure, equations, floats, citations, TODOs, opening sentences. Also regenerates `labels.md`; a `.bib` edit warns about missing `reviews/<key>.yaml` |

The stub is what the interface-first read gate hands back in place of the source ([`../SPECS.md`](../SPECS.md) § One dispatcher), so a language with no row here has that gate switched **off** for its files — `read/pre-read.py` says so out loud rather than passing silently.

## Lifting the size cap while you work

**Edit `BLOCK_LINES` in [`../limits.env`](../limits.env), do the operation, revert.** Both `checks/size-gate.py` and `checks/line_counts.py` read it immediately, so there is no second switch and no per-file exemption to forget to remove. That is the only supported bypass: a marker on the file would outlive the operation, which is how an exemption becomes a permanent one.
