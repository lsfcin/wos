# Setup — interface generators and linters
> The outside programs the edit-time and commit-time gates shell out to: the stub generators that
> produce what the read gate hands an agent instead of a source file, the TypeScript linter, and the
> LaTeX toolchain the paper checks need. Skip one and its gate stops firing rather than failing.
> feature: interface-stubs, lint-typescript, latex
> enforced-by: core/tools/test/workspace/test_setup_executable.py

The five-part contract: [`SETUP.md`](SETUP.md). A missing generator turns its gate off **silently**,
which is why each Verify below produces output rather than a version string.

<!-- steps:start -->

## Python interfaces — stubgen
> feature: `interface-stubs` · agent: yes

Generates the `.pyi` stubs the read gate hands an agent instead of a source file.

`stubgen` is a console script inside the venv and has no `-m` form, so it is located rather than
spelled: `sh core/run --script stubgen` prints its path on any machine.

**Precondition** `"$(sh core/run --script stubgen)" --version`

**Install**
```bash
"$(sh core/run --python)" -m pip install mypy
```

**Verify** `"$(sh core/run --script stubgen)" -o "$(mktemp -d)" core/hooks/file_law.py` — it must
produce a stub, not merely answer `--version`.

## TypeScript interfaces — tsc
> feature: `interface-stubs` · agent: yes

The hook checks `tsc` on `PATH` first, then `~/.local/bin/tsc`, so either location works.

**Precondition** `tsc --version || ~/.local/bin/tsc --version`

**Install** — needs Node (`node --version`); install it with `nvm` if absent:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc && nvm install --lts
npm install -g typescript                    # if this needs sudo: --prefix ~/.local
```

**Verify** `tsc --version`

## ESLint + Prettier for TypeScript projects
> feature: `lint-typescript` · agent: yes

Project-local, in every TS project carrying an `eslint.config.js`; each imports `code/eslint.shared.js`
and runs via `node_modules/.bin/eslint`. No global install.

**Precondition** `ls code/isoroll-module/node_modules/.bin/eslint code/voti/node_modules/.bin/eslint`

**Install**
```bash
(cd code/isoroll-module && npm install)
(cd code/voti && npm install)
```

**Verify** — the gate must *bite*, not merely run:
```bash
printf '// test\nconst x = foo(bar());\n' > /tmp/test-lint.ts
(cd code/isoroll-module && node_modules/.bin/eslint /tmp/test-lint.ts)   # expect: 2 calls in one statement
```

## LaTeX toolchain
> feature: `latex` · agent: yes

For `academy/papers/`. The procedure is [`academy/SETUP.md`](academy/SETUP.md), which answers a
question no workspace-level install covers.

**Precondition** `pdflatex --version | head -1`

**Install** — follow [`academy/SETUP.md`](academy/SETUP.md).

**Verify**
```bash
cd academy && make -n 2>/dev/null | head -3 || pdflatex --version | head -1
```

<!-- steps:end -->
