# postedit
> Sourced post-edit stages: regenerate interfaces, remind, sync, lint.

<!-- routing:start -->
## Routing

| File | Description |
|------|-------------|
| [`interfaces.sh`](interfaces.sh) | Regenerate the interface next to the file just edited — .pyi, .d.ts, .dart.api, .texif. Sourced by core/hooks/post-edit.sh — a FRAGMENT, not a standalone script: it relies on $file, $dir, $TSC and find_tsconfig from the caller. |
| [`lint.sh`](lint.sh) | ESLint + Prettier for TypeScript under code/ (R1-R6). Sourced by core/hooks/post-edit.sh — a FRAGMENT, not a standalone script: it relies on $file, $dir, $TSC and find_tsconfig from the caller. |
| [`reminders.sh`](reminders.sh) | Nudges, never blocks: first-line description, facade boundary, CONTEXT.md line 2 and goal link. Sourced by core/hooks/post-edit.sh — a FRAGMENT, not a standalone script: it relies on $file, $dir, $TSC and find_tsconfig from the caller. |
| [`sync.sh`](sync.sh) | Keep generated indexes fresh: the CONTEXT.md routing block and the codegraph. Sourced by core/hooks/post-edit.sh — a FRAGMENT, not a standalone script: it relies on $file, $dir, $TSC and find_tsconfig from the caller. |
<!-- routing:end -->
